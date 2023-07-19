import csv
from collections import defaultdict

# create legenda
with open('scenario_builder.csv') as csv_file:
    legenda = defaultdict(dict)
    rd = csv.DictReader(csv_file, delimiter=';')

    row_count = -1
    for row in rd:
        if row['ID'] != '':
            legenda[row['ID']] = row['Name']
    csv_file.close()

# create scenario map and location of object all_instances
known_all_instances = []
all_instances = defaultdict(dict)
for id, name in legenda.items():
    all_instances[name] = {}

scenario_map = defaultdict(list)
with open('scenario_builder.csv') as csv_file:
    rd = csv.DictReader(csv_file, delimiter=';')
    for row in rd:
        row_count += 1
        # create scenario_map
        for column in row:
            if column.isdigit():
                value = row[column]
                scenario_map[row_count].append(value)
                # add to objects
                if value != '':
                    id_filtered = list(filter(lambda x: x.isalpha(), value))
                    id_filtered = ''.join(id_filtered)
                    if id_filtered in legenda.keys():
                        instance = value
                        name = legenda[id_filtered]
                        if instance not in known_all_instances:
                            known_all_instances.append(instance)
                            all_instances[name].update({instance: {"positions" : []}})
                        all_instances[name][instance]["positions"].append([row_count, column])
    csv_file.close()

# Build AIMS scenario dictionary
scenario_dict = {"world":{}, "rooms":[], "command_post":{}, "victims":[], "human":{}, "earthquakes": []}

# property csv
with open('scenario_properties.csv') as csv_file:
    lower_stream = (line.lower() for line in csv_file)
    properties_csv = csv.DictReader(csv_file, delimiter=';')
    for row["ID"] in properties_csv:
        if row["ID"] != '':
            row_ID = (row["ID"])
            ID = row_ID["ID"]
            for item in row_ID:
                item_lower = str.lower(item)
                if 'property' in item_lower:
                    prop = row_ID[item]
                if "value" in item_lower and row_ID[item] != '':
                    val = row_ID[item]
                    id_filtered = list(filter(lambda x: x.isalpha(), ID))
                    id_filtered = ''.join(id_filtered)
                    upper_class = legenda[id_filtered]
                    all_instances[upper_class][ID].update({prop: val})

# world
shape = [len(scenario_map), len(next(iter(scenario_map.values())))]

scenario_dict["world"]["shape"] = shape
scenario_dict["world"]["tick_duration"] = 0.1
# Todo: read properties from json

# rooms
scenario_dict["rooms"] = []
for room, room_properties in all_instances['rooms'].items():
        for property_name, value in room_properties.items():
            # position and dimension
            if property_name == "positions":
                top_left_row = int(value[0][0])
                top_left_column = int(value[0][1])
                top_right_row = int(value[-1][0])
                top_right_column = int(value[-1][1])
                dimensions = [(top_right_row-top_left_row)+1, (top_right_column-top_left_column)+1]
                scenario_item = {"top_left": [top_left_row,top_left_column], "dimensions": dimensions}

            # other properties
            else:
                scenario_item[property_name] = value

        # add room and its properties to scenario dictionary
        scenario_dict["rooms"].append(scenario_item)

# Todo: Only read locations of objects from csv, and just take their properties from a json.
# Todo: We can then create the environment after obtaining the objects and locations from the csv and add their
# Todo: properties from the json.
# Todo: Let the json be leading -> the json determines what objects should be present. The location is then taken by
# Todo: searching for this object in the csv.

## top_left
## dimensions
## door

# command_post

# victims

# human

# earthquakes

print('Done')


#    legenda[row] = value
    #legenda = {rows[0]: rows[1] for rows in csv_reader}
#    print('Done')
