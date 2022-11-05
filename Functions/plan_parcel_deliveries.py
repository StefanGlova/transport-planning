import csv
import json


def plan_parcel_deliveries() -> json:
    """This is last of planning function, once plan on the fleet is finished, this function will plan smaller orders
    for parcel delivery everywhere where inventory is available

    :return: parcel delivery plan in json format
    """
    with open("Files_temp/not_planned.json", "r") as file:
        to_plan = json.load(file)

    with open("Files_temp/inventory_for_parcel_deliveries.json", "r") as file:
        inventory = json.load(file)

    customers_with_orders_details = {}
    potential_customers = []

    with open("Entry_DATA/orders.csv", "r") as orders_file:
        reader = csv.DictReader(orders_file)

        for row in reader:
            customer = row["Customer"]
            postcode = row["Post_Code"]
            if postcode in to_plan:
                customers_with_orders_details[customer] = []
                potential_customers.append(customer)

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
            sku_available = float(inventory[sku])
            if customer in potential_customers:
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

    planned_volume = {}
    for customer in potential_customers:
        planned_volume[customer] = 0

    for customer in customers_with_orders_details:
        for order in customers_with_orders_details[customer]:
            volume = order["volume_allocated"]
            planned_volume[customer] += volume

    parcel_customers = []
    for customer in planned_volume:
        if planned_volume[customer] >= 0:
            parcel_customers.append(customer)

    helper = dict(customers_with_orders_details)
    customers_with_orders_details = {}
    for customer in helper:
        customers_with_orders_details[customer] = []
        for index in range(len(helper[customer])):
            if helper[customer][index]["volume_allocated"] != 0:
                customers_with_orders_details[customer].append(helper[customer][index])

    drop = 0
    parcel_deliveries = {}

    for customer in parcel_customers:
        if customers_with_orders_details[customer]:
            drop += 1
            load_name = f"{drop} {customer}"
            parcel_deliveries[load_name] = {}
            parcel_deliveries[load_name]["plan"] = []
            parcel_deliveries[load_name]["plan"].append(customers_with_orders_details[customer])
            parcel_deliveries[load_name]["volume"] = planned_volume[customer]

    with open("Outcome/parcel_deliveries.json", "w") as file:
        json.dump(parcel_deliveries, file, indent=4)
    
    
    with open("Functions/final_plan.txt", "a") as file:
        print(f"There are {drop} carrier deliveries.", file=file)    
    

    return "Outcome/parcel_deliveries.json"
