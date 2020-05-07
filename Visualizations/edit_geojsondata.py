from flask import Flask, request
app = Flask(__name__)

import json
from random import randint
import pandas as pd
import sys, os
sys.path.append("../")
from preprocess.process_batches import *
count = 0
countries = []
data = {}

@app.route('/')
def hello_world():
	return "Hello World"

@app.route('/update', methods=['POST'])
def update_geojson_data(count):
	new_batch_data = find_next_batch(count)
	count += len(new_batch_data) + 1
	with open('meningitis_belt.geojson', "r") as json_file:
		data = json.load(json_file)
		for feature in data["features"]:
			feature["properties"]["density"] = 0
			if feature["properties"]["name"] in new_batch_data["Country"].unique():
				feature["properties"]["density"] = int(new_batch_data.loc[new_batch_data.Country == feature["properties"]["name"]]["Cases"].values[0])
	with open("mengeo.geojson", "w") as json_file:
		json.dump(data, json_file, sort_keys = True, indent=1)
	#return count;



#sets up functions to call when this is called as a module
if __name__ == '__main__':
	app.run(debug=True)
