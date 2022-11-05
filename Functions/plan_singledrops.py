import json
import csv


def plan_full_loads(potential_full_loads: list, orders_file: csv, inventory_file: csv, volume_target: float,
                    max_volume: float, customers: list) -> dict:
    """Use "potential_full_loads" list to check if enough inventory is available. If so, plan_of_full_loads full trailer
    loads for delivery. Use qty in inventory_file to check inventory - once planned, reduce qty for further use.

    :param max_volume: is given limitation of vehicle capacity - maximum that can be planned
    :param customers: List of all customers. Global variable in project file.
    :param volume_target: target for minimum volume per vehicle for trip to make economical sense
    :param potential_full_loads: list of customers who have outstanding orders with volume, enough to create
    full loads for delivery
    :param orders_file: file with full list of all orders, which contains following information:
        customer name
        order number
        sku
        qty
        volume information
        post code
    :param inventory_file: file which contain list of all SKUs and available quantity for each of them
    :return: plan_of_full_loads: python dictionary with full load.
    """
    VOLUME_TARGET = volume_target
    MAX_VOLUME = max_volume
    customers = customers

    # from inventory_file, create dictionary which contains sku as key and quantity as value
    inventory = {}

    with open(inventory_file, "r") as inventory_file:
        reader = csv.DictReader(inventory_file)
        for row in reader:
            sku = row["SKU"]
            qty = int(float(row["Qty"]))
            inventory[sku] = qty

    # create variable customers_with_orders_details as python dictionary
    customers_with_orders_details = {}
    for customer in potential_full_loads:
        customers_with_orders_details[customer] = []
    with open(orders_file, "r") as orders_file:
        reader = csv.DictReader(orders_file)
        for row in reader:
            customer = row["Customer"]
            order = row["Order_number"]
            sku = row["SKU"]
            qty = float(row["Qty"])
            volume = float(row["Volume"])
            post_code = row["Post_Code"]
            volume_per_unit = volume / qty
            sku_available = float(inventory[sku])
            if customer in potential_full_loads:
                details = {"order": order, "sku": sku, "qty": qty, "volume": volume, "post_code": post_code,
                           "volume_per_unit": volume_per_unit, "sku_available": sku_available}
                if sku_available >= qty:
                    details["sku_allocated"] = qty
                    inventory[sku] = sku_available - qty
                    details["volume_allocated"] = qty * volume_per_unit
                else:
                    details["sku_allocated"] = sku_available
                    inventory[sku] = 0
                    details["volume_allocated"] = sku_available * volume_per_unit

                customers_with_orders_details[customer].append(details)

    # calculate total volume with allocated inventory for each of potential full load customers
    planned_volume = {}
    for customer in potential_full_loads:
        planned_volume[customer] = 0

    for customer in customers_with_orders_details:
        for order in customers_with_orders_details[customer]:
            volume = order["volume_allocated"]
            planned_volume[customer] += volume

    # create a list of all customers who still meet criteria for full load, after inventory allocation
    full_loads_customers = []
    for customer in planned_volume:
        if planned_volume[customer] >= VOLUME_TARGET:
            full_loads_customers.append(customer)

    # deallocate inventory from customers who does not qualify for full trailer delivery
    # put that stock back to inventory

    for customer in customers_with_orders_details:
        if customer not in full_loads_customers:
            for order in range(len(customers_with_orders_details[customer])):
                qty = customers_with_orders_details[customer][order]["sku_allocated"]
                customers_with_orders_details[customer][order]["sku_allocated"] -= qty
                inventory[customers_with_orders_details[customer][order]["sku"]] += qty

    # remove customers who does not qualify for full load from customers_with_orders_details dictionary
    # also delete them from planned_volume dictionary
    copy_customers_with_orders_details = dict(customers_with_orders_details)
    for customer in copy_customers_with_orders_details:
        if customer not in full_loads_customers:
            customers_with_orders_details.pop(customer)
            planned_volume.pop(customer)

    # change qty on customers_with_orders_details dict to sku_allocated, so only quantity with allocate inventory is
    # in dictionary
    for customer in customers_with_orders_details:
        # print(customer)
        for index in range(len(customers_with_orders_details[customer])):
            # print(customers_with_orders_details[customer][index])
            customers_with_orders_details[customer][index]["qty"] = \
                customers_with_orders_details[customer][index]["sku_allocated"]
            # print(customers_with_orders_details[customer][index])

    # delete all entries from customers_with_orders_details dict where qty = 0
    helper = dict(customers_with_orders_details)
    customers_with_orders_details = {}
    for customer in helper:
        customers_with_orders_details[customer] = []
        for index in range(len(helper[customer])):
            if helper[customer][index]["qty"] != 0:
                customers_with_orders_details[customer].append(helper[customer][index])

    # remove customers who DO qualify for full load from the list of all customers
    helper_customers = []
    for customer in customers:
        if customer not in full_loads_customers:
            helper_customers.append(customer)

    # create variables
    number_of_full_loads = 0
    plan_of_full_loads = {}
    too_big = {}

    # get number of full loads and update number_of_full_loads global variable
    for customer in full_loads_customers:
        if planned_volume[customer] < MAX_VOLUME:
            number_of_full_loads += 1
            load_name = f"{number_of_full_loads} {customer}"
            plan_of_full_loads[load_name] = {}
            plan_of_full_loads[load_name]["plan"] = []
            plan_of_full_loads[load_name]["total_volume"] = 0
            plan_of_full_loads[load_name]["plan"].append(customers_with_orders_details[customer])
            plan_of_full_loads[load_name]["total_volume"] = planned_volume[customer]

        elif MAX_VOLUME <= planned_volume[customer] < 2 * VOLUME_TARGET:
            number_of_full_loads += 1
            load_name = f"{number_of_full_loads} {customer}"
            plan_of_full_loads[load_name] = {}
            plan_of_full_loads[load_name]["plan"] = []
            plan_of_full_loads[load_name]["total_volume"] = 0
            volume_check = 0
            for index in range(len(customers_with_orders_details[customer])):
                if volume_check + customers_with_orders_details[customer][index]["volume_allocated"] \
                        < MAX_VOLUME:
                    plan_of_full_loads[load_name]["plan"].append(customers_with_orders_details[customer][index])
                    volume_check += customers_with_orders_details[customer][index]["volume_allocated"]
                    plan_of_full_loads[load_name]["total_volume"] = volume_check
                else:
                    qty = customers_with_orders_details[customer][index]["sku_allocated"]
                    customers_with_orders_details[customer][index]["sku_allocated"] -= qty
                    customers_with_orders_details[customer][index]["qty"] -= qty
                    inventory[customers_with_orders_details[customer][index]["sku"]] += qty
            plan_of_full_loads[load_name]["total_volume"] = volume_check

        elif 2 * VOLUME_TARGET <= planned_volume[customer] < 2 * MAX_VOLUME:
            volume_target = planned_volume[customer] / 2
            number_of_full_loads += 1
            load_name = f"{number_of_full_loads} {customer}"
            plan_of_full_loads[load_name] = {}
            plan_of_full_loads[load_name]["plan"] = []
            plan_of_full_loads[load_name]["total_volume"] = 0
            volume_check = 0
            already_planned = []
            for index in range(len(customers_with_orders_details[customer])):
                if volume_check + customers_with_orders_details[customer][index]["volume_allocated"] < volume_target:
                    plan_of_full_loads[load_name]["plan"].append(customers_with_orders_details[customer][index])
                    volume_check += customers_with_orders_details[customer][index]["volume_allocated"]
                    planned_order = (customers_with_orders_details[customer][index]["order"],
                                     customers_with_orders_details[customer][index]["sku"])
                    already_planned.append(planned_order)
            plan_of_full_loads[load_name]["total_volume"] = volume_check

            number_of_full_loads += 1
            load_name = f"{number_of_full_loads} {customer}"
            plan_of_full_loads[load_name] = {}
            plan_of_full_loads[load_name]["plan"] = []
            plan_of_full_loads[load_name]["total_volume"] = 0
            volume_check = 0
            for index in range(len(customers_with_orders_details[customer])):
                to_plan = (customers_with_orders_details[customer][index]["order"],
                           customers_with_orders_details[customer][index]["sku"])

                if volume_check + customers_with_orders_details[customer][index]["volume_allocated"] < \
                        volume_target and to_plan not in already_planned:
                    plan_of_full_loads[load_name]["plan"].append(customers_with_orders_details[customer][index])
                    volume_check += customers_with_orders_details[customer][index]["volume_allocated"]
            plan_of_full_loads[load_name]["total_volume"] = volume_check

        elif planned_volume[customer] > 2 * MAX_VOLUME:
            too_big[customer] = planned_volume[customer]
            for index in range(len(customers_with_orders_details[customer])):
                qty = customers_with_orders_details[customer][index]["sku_allocated"]
                customers_with_orders_details[customer][index]["sku_allocated"] -= qty
                customers_with_orders_details[customer][index]["qty"] -= qty
                inventory[customers_with_orders_details[customer][index]["sku"]] += qty

    with open("Outcome/too_big.json", "w") as file:
        json.dump(too_big, file, indent=4)

    with open("Files_temp/inventory.json", "w") as file:
        json.dump(inventory, file, indent=4)

    print("Here is the list of full loads:")
    for load in plan_of_full_loads:
        print("******* ", load, plan_of_full_loads[load]["total_volume"])
        
    with open("Functions/final_plan.txt", "w") as file:
        print("Here is the list of full loads:", file=file)
        for load in plan_of_full_loads:
            print("******* ", load, plan_of_full_loads[load]["total_volume"], file=file)
        print("\n", file=file)
    
    

    print("Here is the list of customers which need to be planned manually, due to excessive volume: ")
    for customer in too_big:
        print("******* ", customer, too_big[customer])
        
    with open("Functions/final_plan.txt", "a") as file:
        print("Here is the list of customers which need to be planned manually, due to excessive volume:", file=file)
        for customer in too_big:
            print("******* ", customer, too_big[customer], file=file)
        print("\n", file=file)    
    

    return plan_of_full_loads
