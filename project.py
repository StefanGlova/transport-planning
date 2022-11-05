import csv
import json
from Functions.plan_singledrops import plan_full_loads
from Functions.distance import calculate_distance_and_savings
from Functions.plan_multidrops import plan_multidrop_loads
from Functions.plan_parcel_deliveries import plan_parcel_deliveries


customers = []


def planning_function(VOLUME_TARGET = 49.0, VOLUME_MAX = 55.0, MINIMUM_VOLUME = 0.35):
    """Main function is creating complex delivery plan. It takes following files as data source:
            1. inventory.csv - with information about inventory
            2. orders.csv - with all orders details by lines for each order
            3. postcodes.csv - is database of all UK postcodes with their latitude and longitude
        Once function is called, it first create process customer information and then plan full loads. As side
        product it creates list of customers who are bigger than 2 loads.
        Then it plans all customers who are not big enough for full load, but still meet minimum volume criteria.
        Then it plans all small customers as parcel delivery.
        During whole process it also allocate inventory for each delivery.
        Function itself does not take any parameter.
        This process is based on The Clarke and Wright savings algorithm, but implemented for manufacturing businesses
        which have inventory / manufacturing limitations, doing re-deliveries if order is not delivered in full,
        allowing smaller volume orders from less then 1 m3 volume up to few 100s m3 volume per order.

    :return: full plan
    """
    global customers


    customers = get_customers("Entry_DATA/orders.csv")
    customer_volume = get_gross_volume_per_customer("Entry_DATA/orders.csv")
    potential_full_loads = large_volume(customer_volume)

    # this function is for customers with volume more than VOLUME_TARGET, but less than 2 * VOLUME_MAX
    # it means for customer who have volume between 1 and 2 full loads.
    # EXTRA outcome from this function is file with customer names, who have volume more than for 2 full
    # trailer which needs to be planned manually
    full_loads_plan = plan_full_loads(potential_full_loads, "Entry_DATA/orders.csv", "Entry_DATA/inventory.csv",
                                      VOLUME_TARGET, VOLUME_MAX, customers)
    create_json_file("Outcome/full_loads", full_loads_plan)
    create_json_file("Files_temp/not_planned_yet", sorted(customers))

    #calculate_distance_and_savings()

    # this function is for customers with volume less than VOLUME_TARGET, but more than MINIMUM_VOLUME
    # it means for customer have more than minimum order volume, but do not have enough for a full trailer
    plan_multidrop_loads(MINIMUM_VOLUME, VOLUME_TARGET, VOLUME_MAX)

    # this function will plan all small deliveries, which has not meet MINIMUM_VOLUME target and inventory is available
    plan_parcel_deliveries()



def get_customers(orders_file: csv) -> list:
    """Function which reads csv file with all order details and return list of unique customer names

    :param orders_file: Required. File with full list of all orders, which contains following information:
        customer name
        order number
        sku
        qty
        volume information
        post code
    :return: List called "customers" which contains unique customer names.
    """
    customers_list = []
    with open(orders_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            customer = row["Customer"]
            if customer not in customers_list:
                customers_list.append(customer)

    return customers_list


def get_gross_volume_per_customer(orders_file: csv) -> dict:
    """Function which use list of customers and csv file with all order details. Function creates dictionary
    "customer_volume", which will keep reading through csv file and keep adding volume information for each customer.

    :param orders_file: Required. File with full list of all orders, which contains following information:
        customer name
        order number
        sku
        qty
        volume information
        post code
    :return: Dict with key value pairs - Key is customer name and value is total volume on order.
    """
    global customers
    customer_volume = {}
    for customer in customers:
        customer_volume[customer] = 0
    with open(orders_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            customer = row["Customer"]
            volume = float(row["Volume"])
            customer_volume[customer] += volume

    return customer_volume


def large_volume(customer_volume: dict) -> list:
    """Function will iterate through customer_volume dictionary and separate all customers who qualify for full load
    delivery.

    :param customer_volume: Dictionary containing customers and volume of their outstanding orders.
    :return: list called "potential_full" which will contain names of all customers who qualify for full load delivery.
    """
    potential_full = []
    for customer in customer_volume:
        volume = float(customer_volume[customer])
        if volume > 50.0:
            potential_full.append(customer)

    return potential_full


def create_json_file(file_name: str, plan) -> json:
    """function takes name of future file and source dictionary as an argument to generate json file

    :param file_name: Required. Name of future file as an string
    :param plan: Optional. source of information which need to be written to the file as python dictionary or
                    python list
    :return: json file
    """
    with open(f"{file_name}.json", "w") as file:
        json.dump(plan, file, indent=4)

    return f"{file_name}.json"


#if __name__ == "__main__":
#    main()
