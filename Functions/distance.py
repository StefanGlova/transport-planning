import csv
import json
import math

ORIGIN_LAT = 53.484253
ORIGIN_LONG = -1.18073
CIRCUITY_FACTOR = 1.2


def calculate_distance_and_savings():
    """This is main function, calling all functions needed to process postcode data, calculate distance between
    all postcodes pair, calculate distance from origin from each postcode and also to calculate saving, if
    two postcodes are used together. It is based on The Clarke and Wright savings algorithm.

    :return: functions called by this main function have their individual returns
    """
    # get a list of postcodes. Return list:
    postcodes1 = get_list_of_postcodes()

    # get latitude and longitude. Return json file co_ordinates.json
    get_lat_long(postcodes1, "Functions/postcodes.csv")

    # create postcode pairs. Return list of list pairs
    postcodes_pairs1 = create_postcodes_pairs(postcodes1)

    # calculate distance between postcodes in postcodes pairs. Return dict + create json file distance.json
    calculate_distance("Files_temp/co_ordinates.json", postcodes_pairs1)

    # calculate distance from origin for each postcode. Return dict + create json file distance_from_origin.json
    calculate_distance_from_origin("Files_temp/co_ordinates.json", postcodes1)
    calculate_saving("Files_temp/distance.json", "Files_temp/distance_from_origin.json")


def get_list_of_postcodes() -> list:
    """function opens csv file with order details and extract all unique postcodes.

    :return: list of unique postcodes
    """
    orders_file = "Entry_DATA/orders.csv"
    postcodes_list = []
    with open(orders_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            postcode = row["Post_Code"]
            postcodes_list.append(postcode)

    postcodes_list = list(set(postcodes_list))

    return postcodes_list


def get_lat_long(postcodes_list: list, postcodes_file: csv) -> json:
    """This function get latitude and longitude for each postcode

    :param postcodes_list: list of postcodes which are going to be used further
    :param postcodes_file: database of all UK postcodes
    :return:
    """
    postcodes1 = postcodes_list
    postcodes_file = postcodes_file
    co_ordinates = {}

    with open(postcodes_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            post_code = row["Postcode"]
            lat = row["Latitude"]
            long = row["Longitude"]
            if post_code in postcodes1:
                co_ordinates[post_code] = {"lat": float(lat), "long": float(long)}

    # postcodes not in postcode file
    co_ordinates["NN3 6RZ"] = {"lat": 52.275103, "long": -0.871138}
    co_ordinates["MK45 6AW"] = {"lat": 52.086866, "long": -0.483272}
    co_ordinates["LN2 4ZT"] = {"lat": 53.241574, "long": -0.491802}

    with open("Files_temp/co_ordinates.json", "w") as file:
        json.dump(co_ordinates, file, indent=4)

    return "Files_temp/co_ordinates.json"


def create_postcodes_pairs(postcodes_list: list) -> list:
    """generate unique postcodes pairs from given list of postcodes.

    :param postcodes_list: Required. List of postcodes.
    :return: List of tuples - each tuple is unique postcodes pair.
    """
    postcodes_pairs_prep = []
    postcodes_pairs = []
    postcodes1 = postcodes_list
    count = 0
    for postcode in postcodes1:
        for pcode in postcodes1:
            if postcode != pcode:
                pair = sorted([postcode, pcode])
                pair = f"{pair[0]}+{pair[1]}"
                count += 1
                postcodes_pairs_prep.append(pair)

    postcodes_pairs_prep = list(set(postcodes_pairs_prep))

    for pair in postcodes_pairs_prep:
        split_pair = pair.split("+")
        p1 = split_pair[0]
        p2 = split_pair[1]
        pair = [p1, p2]
        postcodes_pairs.append(pair)

    with open("Files_temp/pairs.json", "w") as file:
        json.dump(postcodes_pairs, file, indent=4)

    return postcodes_pairs


def calculate_distance(co_ordinates: json, postcodes_pairs: list) -> dict:
    """This function calculate distance between two given postcodes, using their latitude and longitude

    :param co_ordinates: dataset with latitude and longitude for each postcode in json format
    :param postcodes_pairs: all unique postcode pairs for given postcodes
    :return:
    """
    distance = {}
    with open(co_ordinates, "r") as file:
        coordinates = json.load(file)

    for pair in postcodes_pairs:
        P1 = pair[0]
        P2 = pair[1]
        pair = f"{P1}+{P2}"

        p1LAT = coordinates[P1]["lat"]
        p1LONG = coordinates[P1]["long"]
        p2LAT = coordinates[P2]["lat"]
        p2LONG = coordinates[P2]["long"]
        distance[pair] = 3959 * (math.acos(math.sin(p1LAT * math.pi / 180) * math.sin(p2LAT * math.pi / 180)
                                           + math.cos(p1LAT * math.pi / 180) * math.cos(p2LAT * math.pi / 180)
                                           * math.cos(p1LONG * math.pi / 180 - p2LONG * math.pi / 180)
                                           )) * CIRCUITY_FACTOR

    with open("Files_temp/distance.json", "w") as file:
        json.dump(distance, file, indent=4)

    return distance


def calculate_distance_from_origin(co_ordinates: json, postcodes: list) -> dict:
    """This function calculate distance from origin for each given postcode

    :param co_ordinates: dataset with latitude and longitude for each postcode in json format
    :param postcodes: all unique postcode pairs for given postcodes
    :return:
    """
    distance_from_origin = {}
    with open(co_ordinates, "r") as file:
        coordinates = json.load(file)

    for postcode in postcodes:
        p1LAT = coordinates[postcode]["lat"]
        p1LONG = coordinates[postcode]["long"]
        p2LAT = ORIGIN_LAT
        p2LONG = ORIGIN_LONG
        distance_from_origin[postcode] = 3959 * (
            math.acos(math.sin(p1LAT * math.pi / 180) * math.sin(p2LAT * math.pi / 180)
                      + math.cos(p1LAT * math.pi / 180) * math.cos(p2LAT * math.pi / 180)
                      * math.cos(p1LONG * math.pi / 180 - p2LONG * math.pi / 180)
                      )) * CIRCUITY_FACTOR

    with open("Files_temp/distance_from_origin.json", "w") as file:
        json.dump(distance_from_origin, file, indent=4)

        return distance_from_origin


def calculate_saving(distance: json, distance_from_origin: json) -> json:
    """This function calculated saving, if two postcodes are delivered together

    :param distance: distance between postcode pairs
    :param distance_from_origin: distance from origin
    :return:
    """
    saving = {}
    savings = {}
    with open(distance, "r") as file:
        distance = json.load(file)

    with open(distance_from_origin, "r") as file:
        distance_from_origin = json.load(file)

    for item in distance:
        p1 = item.split("+")[0]
        p2 = item.split("+")[1]
        p1_from_origin = distance_from_origin[p1]
        p2_from_origin = distance_from_origin[p2]

        saving[item] = p1_from_origin + p2_from_origin - distance[item]

    s = sorted(saving.items(), key=lambda x: x[1], reverse=True)
    for item in s:
        key = item[0]
        value = item[1]
        savings[key] = value

    with open("Files_temp/savings.json", "w") as file:
        json.dump(savings, file, indent=4)

    return "Files_temp/savings.json"
