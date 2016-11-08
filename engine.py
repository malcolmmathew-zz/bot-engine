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
