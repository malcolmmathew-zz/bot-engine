"""
	Engine for parsing JSON and generating control flow for chatbot webhook. 

	Thoughts
	--------
	- how do we correctly store chat-user responses; do we ask the engine-user
	to define storage elements (e.g. db collections, objects)?
	- it makes most sense for message responses (i.e. user response to an
	emitted message from a list) to be stored in a database
		- the exception to this would be binary answers used to handle
		control flow
	- we need an overarching unique identifier for a user => used when updating
	record attributes
	- we want keys/fields in JSON to be verbose


	Example JSON
	------------
	- database configuration
	{
		"collections": [
			"user",
			"transactions"
		]
	}

	- bot flow configuration
	{
		"default": {
			"type": "carousel",
			"buttons": [
				{
					"name": "log_x",
					"target": <node_uid>,
					"storage": <collection_name>
				},
				{
					"name": "log_y",
					"target": <node_uid>,
					"storage": <collection_name>
				}, 
				{
					"name": "help",
					"target": "help_message",
					"storage": null
				}
			]
		},
		"onboarding": {
			"type": "message_list",
			"messages": [
				{
					"message": "Hello, welcome to ...",
					"expected_input": <input_type>,
					"storage": <collection_name.attribute>
				}, 
				{
					"message": "Please enter your age.",
					"expected_input": int,
					"storage": "user.age"
				},
				{
					"message": "Great, please enter __",
					"expected_input": int,
					"storage": <collection_name.attribute>
				}
			],
			"target": <node_uid>
		},
		"help_message": {
			"type": "message_list",
			"messages": [
				"Generic help message. Something about a keyword that 
				automagically generates the default carousel."
			]
		}
	}
"""
import json
import os

from pymongo import MongoClient


class Engine: 
	"""
		Primary engine class for parsing JSON into application logic.
	"""
	def __init__(self, user_id, json_string):
		"""
			Constructor. Also handles database configuration.

			Parameters
			----------
			user_id : {string}
				alphanumeric identifier for user requiring engine

			json_string : {JSON}
				data obtained from multiple sources in JSON format.
		"""
		self.json_data = json.loads(json_string)
		
		self.client = MongoClient(os.environ["MONGO_IP"], 
								  os.environ["MONGO_PORT"])

		self.db = self.client[user_id]


	def database_config(self):
		"""
			Database configuration parser. Currently used to create
			database collections and insert placeholder records.

			Only reason we create collections is for safety during record
			insertions.
		"""
		db_config = self.json_data["database_configuration"]

		for coll in db_config["collections"]:
			self.db[coll].insert({"record": "placecholder"})


if __name__ == '__main__':
	# create dict, convert to JSON and then parse

	test_data = {
		"database_configuration" : {
			"collections" : ["user", "transactions"]
		}
	}

	json_data = json.dumps(test_data)

	bot_engine = Engine("sunnithan95", json_data)
