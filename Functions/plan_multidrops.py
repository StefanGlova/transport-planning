import csv
import json


def plan_multidrop_loads(minimum_volume: float, volume_target: float, volume_max: float) -> json:
    """This is complex function which plan loads with multiple delivery point, based on
    The Clarke and Wright savings algorithm, but modified with additional functionality with
    stock re-allocation

    :param volume_max: is given limitation of vehicle capacity - maximum that can be planned
    :param volume_target: target for minimum volume per vehicle for trip to make economical sense
    :param minimum_volume: minimum target per delivery point
    :return: json file with complex delivery plan
    """
    # get a list of all customers who does not have planned delivery yet
    with open("Files_temp/not_planned_yet.json", "r") as file:
        customers_list = json.load(file)

    # from inventory_file, create dictionary which contains sku as key and quantity as value
    with open("Files_temp/inventory.json", "r") as inventory_file:
        inventory = json.load(inventory_file)

    # create variable customers_with_orders_details as python dictionary
    customers_with_orders_details = {}
    customers_and_postcodes = {}
    postcodes = []
    for customer in customers_list:
        customers_with_orders_details[customer] = []
    with open("Entry_DATA/orders.csv", "r") as orders_file:
        reader = csv.DictReader(orders_file)
        for row in reader:
            customer = row["Customer"]
            order = row["Order_number"]
            sku = row["SKU"]
            qty = float(row["Qty"])
            volume = float(row["Volume"])
            post_code = row["Post_Code"]
            volume_per_unit = volume / qty
            sku_allocated = 0.0
            volume_allocated = 0.0
            if customer in customers_list:
                details = {"order": order, "sku": sku, "qty": qty, "volume": volume, "post_code": post_code,
                           "volume_per_unit": volume_per_unit, "sku_allocated": sku_allocated,
                           "volume_allocated": volume_allocated}

                customers_with_orders_details[customer].append(details)
                customers_and_postcodes[customer] = post_code
                postcodes.append(details["post_code"])

    postcodes = list(set(postcodes))

    # pre-plan empty dictionary for final plan - up to 199 loads
    plan_of_multidrop_loads = {}
    for number in range(1, 1000):
        plan_of_multidrop_loads[number] = {}
        plan_of_multidrop_loads[number]["plan"] = []
        plan_of_multidrop_loads[number]["total_volume"] = 0
        plan_of_multidrop_loads[number]["count_customers"] = 0

    # variables
    load_count = 1
    planned_volume = 0
    volume_target = volume_target
    volume_max = volume_max
    minimum_volume = minimum_volume
    planned_postcodes = []
    not_planned_postcodes = []
    current_postcodes = []
    count_customers = 0

    # get a dictionary with savings per postcode combinations + copy of the same file for iteration purpose
    with open("Files_temp/savings.json", "r") as file:
        savings = json.load(file)

    for element in savings:
        load_not_full = True
        last_load = False
        postcode1 = element.split("+")[0]
        postcode2 = element.split("+")[1]
        if postcode1 in postcodes and postcode2 in postcodes:
            for customer1 in customers_and_postcodes:

                if postcode1 == customers_and_postcodes[customer1]:
                    allocated_volume_for_first_customer = 0.0
                    for order in range(len(customers_with_orders_details[customer1])):
                        sku = customers_with_orders_details[customer1][order]["sku"]
                        qty = customers_with_orders_details[customer1][order]["qty"]
                        volume_per_unit = customers_with_orders_details[customer1][order]["volume_per_unit"]
                        sku_available = inventory[sku]
                        if sku_available >= qty:
                            customers_with_orders_details[customer1][order]["sku_allocated"] = qty
                            inventory[sku] -= qty
                            customers_with_orders_details[customer1][order]["volume_allocated"] = qty * volume_per_unit
                            allocated_volume_for_first_customer += (qty * volume_per_unit)
                        else:
                            customers_with_orders_details[customer1][order]["sku_allocated"] = sku_available
                            inventory[sku] = 0
                            customers_with_orders_details[customer1][order][
                                "volume_allocated"] = sku_available * volume_per_unit
                            allocated_volume_for_first_customer += (sku_available * volume_per_unit)
                    if allocated_volume_for_first_customer >= minimum_volume \
                            and planned_volume + allocated_volume_for_first_customer <= volume_max:

                        for customer2 in customers_and_postcodes:
                            if postcode2 == customers_and_postcodes[customer2]:
                                allocated_volume_for_second_customer = 0.0
                                for order in range(len(customers_with_orders_details[customer2])):
                                    sku = customers_with_orders_details[customer2][order]["sku"]
                                    qty = customers_with_orders_details[customer2][order]["qty"]
                                    volume_per_unit = customers_with_orders_details[customer2][order]["volume_per_unit"]
                                    sku_available = inventory[sku]
                                    if sku_available >= qty:
                                        customers_with_orders_details[customer2][order]["sku_allocated"] = qty
                                        inventory[sku] = sku_available - qty
                                        customers_with_orders_details[customer2][order][
                                            "volume_allocated"] = qty * volume_per_unit
                                        allocated_volume_for_second_customer += (qty * volume_per_unit)
                                    else:
                                        customers_with_orders_details[customer2][order]["sku_allocated"] = sku_available
                                        inventory[sku] = 0
                                        customers_with_orders_details[customer2][order][
                                            "volume_allocated"] = sku_available * volume_per_unit
                                        allocated_volume_for_second_customer += (sku_available * volume_per_unit)

                                if allocated_volume_for_second_customer >= minimum_volume \
                                        and planned_volume + allocated_volume_for_first_customer \
                                        + allocated_volume_for_second_customer <= volume_max:

                                    plan_of_multidrop_loads[load_count]["plan"].append(customers_with_orders_details[
                                                                                           customer1])
                                    count_customers += 1
                                    plan_of_multidrop_loads[load_count]["plan"].append(customers_with_orders_details[
                                                                                           customer2])
                                    count_customers += 1

                                    planned_volume = planned_volume + allocated_volume_for_first_customer \
                                                     + allocated_volume_for_second_customer
                                    if postcode1 in postcodes:
                                        postcodes.remove(postcode1)
                                    if postcode1 not in planned_postcodes:
                                        planned_postcodes.append(postcode1)
                                    if postcode2 in postcodes:
                                        postcodes.remove(postcode2)
                                    if postcode2 not in planned_postcodes:
                                        planned_postcodes.append(postcode2)

                                    if planned_volume >= volume_target:
                                        plan_of_multidrop_loads[load_count]["total_volume"] = planned_volume
                                        plan_of_multidrop_loads[load_count]["count_customers"] = count_customers
                                        planned_volume = 0
                                        count_customers = 0
                                        load_count += 1

                                    else:
                                        if postcode1 not in current_postcodes:
                                            current_postcodes.append(postcode1)
                                        if postcode2 not in current_postcodes:
                                            current_postcodes.append(postcode2)

                                        while load_not_full is True and last_load is False:
                                            for nested_element in savings:
                                                if not load_not_full or last_load:
                                                    break

                                                postcodeA = nested_element.split("+")[0]
                                                postcodeB = nested_element.split("+")[1]

                                                if (postcodeA in current_postcodes and postcodeB in
                                                    postcodes) or (postcodeB in current_postcodes and
                                                                   postcodeA in postcodes):

                                                    if postcodeB in current_postcodes and postcodeA in postcodes:

                                                        for customerA in customers_and_postcodes:
                                                            if postcodeA == customers_and_postcodes[customerA]:
                                                                allocated_volume_for_A_customer = 0.0
                                                                for order in range(
                                                                        len(customers_with_orders_details[customerA])):
                                                                    sku = \
                                                                        customers_with_orders_details[customerA][order][
                                                                            "sku"]
                                                                    qty = \
                                                                        customers_with_orders_details[customerA][order][
                                                                            "qty"]
                                                                    volume_per_unit = \
                                                                        customers_with_orders_details[customerA][order][
                                                                            "volume_per_unit"]
                                                                    sku_available = inventory[sku]
                                                                    if sku_available >= qty:
                                                                        customers_with_orders_details[customerA][order][
                                                                            "sku_allocated"] = qty
                                                                        inventory[sku] = sku_available - qty
                                                                        customers_with_orders_details[customerA][order][
                                                                            "volume_allocated"] = qty * volume_per_unit
                                                                        allocated_volume_for_A_customer += (
                                                                                qty * volume_per_unit)
                                                                    else:
                                                                        customers_with_orders_details[customerA][order][
                                                                            "sku_allocated"] = sku_available
                                                                        inventory[sku] = 0
                                                                        customers_with_orders_details[customerA][order][
                                                                            "volume_allocated"] = sku_available \
                                                                                                  * volume_per_unit
                                                                        allocated_volume_for_A_customer += (
                                                                                sku_available * volume_per_unit)
                                                                if allocated_volume_for_A_customer >= minimum_volume \
                                                                        and planned_volume \
                                                                        + allocated_volume_for_A_customer <= volume_max:

                                                                    plan_of_multidrop_loads[load_count]["plan"].append(
                                                                        customers_with_orders_details[
                                                                            customerA])
                                                                    count_customers += 1

                                                                    planned_volume = planned_volume \
                                                                                     + allocated_volume_for_A_customer
                                                                    if postcodeA in postcodes:
                                                                        postcodes.remove(postcodeA)
                                                                    if postcodeA not in planned_postcodes:
                                                                        planned_postcodes.append(postcodeA)

                                                                    if planned_volume >= volume_target:
                                                                        plan_of_multidrop_loads[load_count][
                                                                            "total_volume"] = planned_volume
                                                                        plan_of_multidrop_loads[load_count][
                                                                            "count_customers"] = count_customers
                                                                        count_customers = 0
                                                                        planned_volume = 0
                                                                        load_count += 1
                                                                        current_postcodes = []
                                                                        load_not_full = False
                                                                        break

                                                                    else:
                                                                        if postcodeA not in current_postcodes:
                                                                            current_postcodes.append(postcodeA)

                                                                elif allocated_volume_for_A_customer >= minimum_volume \
                                                                        and planned_volume \
                                                                        + allocated_volume_for_A_customer > volume_max:

                                                                    for order in range(
                                                                            len(customers_with_orders_details[
                                                                                    customerA])):
                                                                        qty = \
                                                                            customers_with_orders_details[customerA][
                                                                                order][
                                                                                "sku_allocated"]

                                                                        customers_with_orders_details[customerA][order][
                                                                            "sku_allocated"] -= qty
                                                                        inventory[
                                                                            customers_with_orders_details[customerA][
                                                                                order]["sku"]] += qty
                                                                        customers_with_orders_details[customerA][order][
                                                                            "volume_allocated"] = 0.0

                                                                elif allocated_volume_for_first_customer \
                                                                        < minimum_volume:
                                                                    if postcodeA in postcodes:
                                                                        postcodes.remove(postcodeA)
                                                                    if postcodeA not in not_planned_postcodes:
                                                                        not_planned_postcodes.append(postcodeA)

                                                                    for order in range(
                                                                            len(customers_with_orders_details[
                                                                                    customerA])):
                                                                        qty = \
                                                                            customers_with_orders_details[customerA][
                                                                                order][
                                                                                "sku_allocated"]

                                                                        customers_with_orders_details[customerA][order][
                                                                            "sku_allocated"] -= qty
                                                                        inventory[
                                                                            customers_with_orders_details[customerA][
                                                                                order]["sku"]] += qty
                                                                        customers_with_orders_details[customerA][order][
                                                                            "volume_allocated"] = 0.0

                                                    if postcodeA in current_postcodes and postcodeB in postcodes:

                                                        for customerB in customers_and_postcodes:
                                                            if postcodeB == customers_and_postcodes[customerB]:
                                                                allocated_volume_for_B_customer = 0.0
                                                                for order in range(len(
                                                                        customers_with_orders_details[
                                                                            customerB])):
                                                                    sku = \
                                                                        customers_with_orders_details[customerB][
                                                                            order]["sku"]
                                                                    qty = \
                                                                        customers_with_orders_details[customerB][
                                                                            order]["qty"]
                                                                    volume_per_unit = \
                                                                        customers_with_orders_details[customerB][
                                                                            order]["volume_per_unit"]
                                                                    sku_available = inventory[sku]
                                                                    if sku_available >= qty:
                                                                        customers_with_orders_details[
                                                                            customerB][order][
                                                                            "sku_allocated"] = qty
                                                                        inventory[sku] = sku_available - qty
                                                                        customers_with_orders_details[
                                                                            customerB][order][
                                                                            "volume_allocated"] = qty * volume_per_unit
                                                                        allocated_volume_for_B_customer += (
                                                                                qty * volume_per_unit)
                                                                    else:
                                                                        customers_with_orders_details[
                                                                            customerB][order][
                                                                            "sku_allocated"] = sku_available
                                                                        inventory[sku] = 0
                                                                        customers_with_orders_details[
                                                                            customerB][order][
                                                                            "volume_allocated"] = sku_available \
                                                                                                  * volume_per_unit
                                                                        allocated_volume_for_B_customer += (
                                                                                sku_available * volume_per_unit)

                                                                if allocated_volume_for_B_customer >= minimum_volume \
                                                                        and planned_volume \
                                                                        + allocated_volume_for_B_customer <= volume_max:

                                                                    plan_of_multidrop_loads[load_count]["plan"].append(
                                                                        customers_with_orders_details[
                                                                            customerB])
                                                                    count_customers += 1
                                                                    planned_volume = planned_volume \
                                                                                     + allocated_volume_for_B_customer

                                                                    if postcodeB in postcodes:
                                                                        postcodes.remove(postcodeB)
                                                                    if postcodeB not in planned_postcodes:
                                                                        planned_postcodes.append(postcodeB)

                                                                    if planned_volume >= volume_target:
                                                                        plan_of_multidrop_loads[load_count][
                                                                            "total_volume"] = planned_volume
                                                                        plan_of_multidrop_loads[load_count][
                                                                            "count_customers"] = count_customers
                                                                        count_customers = 0
                                                                        load_count += 1
                                                                        planned_volume = 0
                                                                        current_postcodes = []
                                                                        load_not_full = False
                                                                        break

                                                                    else:
                                                                        if postcodeB not in current_postcodes:
                                                                            current_postcodes.append(postcodeB)

                                                                elif allocated_volume_for_B_customer >= minimum_volume \
                                                                        and planned_volume \
                                                                        + allocated_volume_for_B_customer > volume_max:

                                                                    for order in range(len(
                                                                            customers_with_orders_details[
                                                                                customerB])):
                                                                        qty = customers_with_orders_details[
                                                                            customerB][order]["sku_allocated"]

                                                                        customers_with_orders_details[
                                                                            customerB][order][
                                                                            "sku_allocated"] -= qty
                                                                        inventory[customers_with_orders_details[
                                                                            customerB][order]["sku"]] += qty
                                                                        customers_with_orders_details[
                                                                            customerB][order]["volume_allocated"] = 0.0

                                                                elif allocated_volume_for_B_customer < minimum_volume:
                                                                    if postcodeB in postcodes:
                                                                        postcodes.remove(postcodeB)
                                                                    if postcodeB not in not_planned_postcodes:
                                                                        not_planned_postcodes.append(postcodeB)

                                                                    for order in range(len(
                                                                            customers_with_orders_details[
                                                                                customerB])):
                                                                        qty = customers_with_orders_details[
                                                                            customerB][order]["sku_allocated"]

                                                                        customers_with_orders_details[
                                                                            customerB][order][
                                                                            "sku_allocated"] -= qty
                                                                        inventory[customers_with_orders_details[
                                                                            customerB][order]["sku"]] += qty
                                                                        customers_with_orders_details[
                                                                            customerB][order]["volume_allocated"] = 0.0

                                            plan_of_multidrop_loads[load_count][
                                                "total_volume"] = planned_volume
                                            plan_of_multidrop_loads[load_count][
                                                "count_customers"] = count_customers
                                            last_load = True

                                elif allocated_volume_for_second_customer >= minimum_volume \
                                        and planned_volume + allocated_volume_for_first_customer \
                                        + allocated_volume_for_second_customer > volume_max:

                                    for order in range(len(customers_with_orders_details[customer1])):
                                        qty = customers_with_orders_details[customer1][order]["sku_allocated"]
                                        customers_with_orders_details[customer1][order]["sku_allocated"] -= qty
                                        inventory[customers_with_orders_details[customer1][order]["sku"]] += qty
                                        customers_with_orders_details[customer1][order]["volume_allocated"] = 0.0
                                    
                                    for order in range(len(customers_with_orders_details[customer2])):
                                        qty = customers_with_orders_details[customer2][order]["sku_allocated"]
                                        customers_with_orders_details[customer2][order]["sku_allocated"] -= qty
                                        inventory[customers_with_orders_details[customer2][order]["sku"]] += qty
                                        customers_with_orders_details[customer2][order]["volume_allocated"] = 0.0


                                elif allocated_volume_for_second_customer < minimum_volume:
                                    if postcode2 in postcodes:
                                        postcodes.remove(postcode2)
                                    if postcode2 not in not_planned_postcodes:
                                        not_planned_postcodes.append(postcode2)

                                    for order in range(len(customers_with_orders_details[customer2])):
                                        qty = customers_with_orders_details[customer2][order]["sku_allocated"]
                                        customers_with_orders_details[customer2][order]["sku_allocated"] -= qty
                                        inventory[customers_with_orders_details[customer2][order]["sku"]] += qty
                                        customers_with_orders_details[customer2][order]["volume_allocated"] = 0.0

                                    for order in range(len(customers_with_orders_details[customer1])):
                                        qty = customers_with_orders_details[customer1][order]["sku_allocated"]
                                        customers_with_orders_details[customer1][order]["sku_allocated"] -= qty
                                        inventory[customers_with_orders_details[customer1][order]["sku"]] += qty
                                        customers_with_orders_details[customer1][order]["volume_allocated"] = 0.0

                    elif allocated_volume_for_first_customer >= minimum_volume \
                            and planned_volume + allocated_volume_for_first_customer > volume_max:

                        for order in range(len(customers_with_orders_details[customer1])):
                            qty = customers_with_orders_details[customer1][order]["sku_allocated"]
                            customers_with_orders_details[customer1][order]["sku_allocated"] -= qty
                            inventory[customers_with_orders_details[customer1][order]["sku"]] += qty
                            customers_with_orders_details[customer1][order]["volume_allocated"] = 0.0

                    elif allocated_volume_for_first_customer < minimum_volume:
                        if postcode1 in postcodes:
                            postcodes.remove(postcode1)
                        if postcode1 not in not_planned_postcodes:
                            not_planned_postcodes.append(postcode1)

                        for order in range(len(customers_with_orders_details[customer1])):
                            qty = customers_with_orders_details[customer1][order]["sku_allocated"]
                            customers_with_orders_details[customer1][order]["sku_allocated"] -= qty
                            inventory[customers_with_orders_details[customer1][order]["sku"]] += qty
                            customers_with_orders_details[customer1][order]["volume_allocated"] = 0.0

    with open("Outcome/finished_plan.json", "w") as file:
        json.dump(plan_of_multidrop_loads, file, indent=4)

    with open("Files_temp/not_planned.json", "w") as file:
        json.dump(not_planned_postcodes, file, indent=4)

    with open("Files_temp/planned_orders.json", "w") as file:
        json.dump(planned_postcodes, file, indent=4)

    with open("Files_temp/inventory_for_parcel_deliveries.json", "w") as file:
        json.dump(inventory, file, indent=4)

    with open("Outcome/finished_plan.json", "r") as file:
        pre_plan = json.load(file)

    with open("Outcome/finished_plan.json", "r") as file:
        helper = json.load(file)

    count = 0
    for load in helper:
        if not helper[load]["plan"]:
            count += 1
            pre_plan.pop(load)

    planned_volume = {}
    for load in pre_plan:
        planned_volume[load] = 0

    for load in pre_plan:
        print(
            f"******* load: {load}, number of drops: {pre_plan[load]['count_customers']}, "
            f"total volume: {pre_plan[load]['total_volume']}")
            
    with open("Functions/final_plan.txt", "a") as file:
        print("Here is multidrop plan:", file=file)
        for load in pre_plan:
            print(
                f"******* load: {load}, number of drops: {pre_plan[load]['count_customers']}, "
                f"total volume: {pre_plan[load]['total_volume']}", file=file)
        print("\n", file=file) 
        
        for load in plan_of_multidrop_loads:
            print(load, plan_of_multidrop_loads[load], file=file)
                

    return "Outcome/finished_plan.json"
