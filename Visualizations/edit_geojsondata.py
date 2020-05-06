import json
from random import seed
from random import randint
seed(1)
count = 0
countries = []
data = {}
with open('meningitis_belt.geojson', "r") as json_file:
	data = json.load(json_file)
	for feature in data["features"]:
		print(feature["properties"])
		feature["properties"]["density"] = randint(0, 100)


with open("men_featuresv2.js", "w") as json_file:
	json.dump(data, json_file, sort_keys = True, indent=1)