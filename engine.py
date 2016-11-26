"""
    Engine for parsing JSON and generating control flow for chatbot webhook. 

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
            "options": [
                {
                    "name": "log_income",
                    "target": "income_amt_prompt"
                },
                {
                    "name": "log_y",
                    "target": <node_uid>
                }, 
                {
                    "name": "help",
                    "target": "help_message"
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
                {
                    "message": "Generic help message."
                }
            ]
        },
        "income_amount_prompt": {
            "type": "message_list",
            "messages": [
                {
                    "message": "How much did you earn today?",
                    "expected_input": float,
                    "storage": "transactions.amount"
                }
            ]
        }
    }
"""
import json
import os
import shutil

from pymongo import MongoClient

import templates as tl
from utils import format_string


class Engine: 
    """
        Primary engine class for parsing JSON into application logic.
    """
    def __init__(self, user_id, json_string, **kwargs):
        """
            Constructor. Also handles database configuration and 
            application logic instantiation.

            Parameters
            ----------
            user_id : {string}
                alphanumeric identifier for user requiring engine       
        
            json_string : {JSON}
                data obtained from multiple sources in JSON format.

            Keyword-Arguments
            -----------------
            page_access_token : {string}
                alphanumeric token used to identify user's page; required for 
                application logic
        
            verification_token : {string}
                alphanumeric token for hub verification; required for 
                application logic

            mongo_host : {string}
                database url; should include appropriate port
        """
        self.user_id = user_id
        self.json_data = json.loads(json_string)
        self.pat = kwargs["page_access_token"]
        self.vt = kwargs["verification_token"]
        self.mongo_host = kwargs["mongo_host"]

        # output file config
        self.output_dir = "output/%s" % self.user_id

        if os.path.exists(self.output_dir):
            # remove existing user directory
            shutil.rmtree(self.output_dir)
        
        # make user directory
        os.makedirs(self.output_dir)

        # database config
        self.client = MongoClient(self.mongo_host)
        self.db = self.client[self.user_id]

        # bot application config
        self.bot_configuration = self.json_data["bot_configuration"]
        self.database_configuration = self.json_data["database_configuration"]

        self.carousels = \
            [(name, data) for name, data in self.bot_configuration.iteritems() 
             if data["type"] == "carousel"]

        self.message_lists = \
            [(name, data) for name, data in self.bot_configuration.iteritems()
             if data["type"] == "message_list"]

    def database_config(self):
        """
            Database configuration parser. Currently used to create
            database collections and insert placeholder records.

            Only reason we create collections is for safety during record
            insertions.
        """
        db_config = self.database_configuration

        db_config.append("state")

        for coll in db_config["collections"]:
            self.db[coll].insert({"record": "placecholder"})


    def webhook_logic(self):
        """
            Method to string together all components of the webhook logic
            (i.e. message, carousel, and quick reply handling).
        """

        # build postback flow 
        # each postback includes a payload check, a state update,
        # possible data insertion, and a message sending action
        postback_container = []

        for name, data in self.carousels:
            for option in data["options"]:
                payload = option["name"].upper()
                target = option["target"]

                # messages that follow postbacks will always be indexed at 0
                target_content = "%s_0" % option["target"] if \
                    self.bot_configuration[option["target"]]["type"] == "message_list" \
                    else option["target"]

                if "storage" in option:
                    data_insertion = \
"""
state_coll.update({"user_id": sender_id}, {
    "$set": {
        "data.%s": message_payload
    }
}, upsert=False)
"""
                    storage = "_".join(option["storage"].split("."))
                    data_insertion = data_insertion % option["storage"]
                
                else:
                    data_insertion = ""

                logic = format_string(tl.postback_logic, 
                                      payload=option["name"].upper(),
                                      target=option["target"], 
                                      data_insertion=data_insertion,
                                      target_content=target_content)

                postback_container.append(logic)

        web_logic = \
            format_string(
                tl.webhook_logic, state_map_template=self.state_creation(),
                postback_control_flow="\n".join(postback_container))

        return web_logic

    def content_creation(self):
        """
            Primary method for bot content creation. Outputs content to separate
            file.
        """
        # temporary standard image url
        image_url = "http://messengerdemo.parseapp.com/img/rift.png"

        carousel_container = []

        car_elems = []

        for name, data in self.carousels:
            for option in data["options"]:
                # parse option specs
                
                title = " ".join(map(lambda x: x[:1].upper() + x[1:],
                                     option["name"].replace("_", " ").split(" ")))

                elem = {
                    "title": title,
                    "image_url": image_url,
                    "buttons": [
                        {
                            "type": "postback",
                            "title": title,
                            "payload": option["name"].replace(" ", "_").upper()
                        }
                    ]
                }

                car_elems.append(elem)

            carousel_container.append(
                format_string(tl.carousel_content_base, name=name, 
                              carousel_elements=car_elems))

        message_list_container = []

        for name, data in self.message_lists:
            # we keep message variable names as <title.index>
            for idx, msg in enumerate(data["messages"]):
                title = "%s_%s" % (name, idx)

                message_list_container.append(
                    format_string(tl.message_content_base, name=title,
                                  message_text=msg["message"]))

        content = format_string(
            tl.content_base, carousels=",\n".join(carousel_container),
            messages=",\n".join(message_list_container))

        # write content to file
        with open("%s/content.py" % self.output_dir, "w") as file:
            file.write(content)

        return True


    def state_creation(self):
        """
            Method to create state object to handle message responses correctly.
            
            Only "nodes" in the message list containers
            Each "node" in the carousel and message list containers should have
            corresponding switches in the state map.
        """
        state_map = {}

        for node, node_data in self.bot_configuration.iteritems():
            if node_data["type"] != "message_list":
                continue

            state_map[node] = {
                "switch": False,
                "index": 0,
                "length" : len(node_data["messages"]),
                "list" : node_data["messages"],
                "target" : node_data["target"]
            }

        state_map["flow_instantiated"] = False

        state_map["previous_type"] = ""

        state_map["data"] = {}

        file_content = \
"""
state_map = ~state_map_content~
"""

        # write state map to file
        with open("%s/state.py" % self.output_dir, "w") as file:
            file.write(format_string(file_content, state_map_content=state_map))

        return state_map


    def logic_creation(self):
        """
            Primary method for bot/application logic creation. Outputs to 
            separate file.
        """

        al = format_string(
            tl.base_application_logic, mongo_host=self.mongo_host,
            user_id=self.user_id, page_access_token=self.pat, 
            verify_token=self.vt, webhook_logic=self.webhook_logic())

        # write content t ofile
        with open("%s/app.py" % self.output_dir, "w") as file:
            file.write(al)

        return True


    def procfile_creation(self):
        """
            Procfile required for Heroku deployment.
        """
        content = \
"""
web: gunicorn app:app --log-file -
"""
    
        # write procfile
        with open("%s/Procfile" % self.output_dir, "w") as file:
            file.write(content)

        return True


    def requirements_creation(self):
        """
            Python-specific requirements file. Contains database, server, and
            application-specific libraries.
        """
        content = \
"""
pymongo
Flask
requests
"""
    
        # write requirements
        with open("%s/requirements.txt" % self.output_dir, "w") as file:
            file.write(content)

        return True


    def process(self):
        """
            Primary method to handle engine process. Calls member function in
            particular order. The end results are application and content files
            deployed and configured for the engine-user's facebook page.
        """

        self.database_config()

        self.content_creation()

        self.logic_creation()

        self.procfile_creation()

        self.requirements_creation()

        return self.user_id


if __name__ == '__main__':
    # create dict, convert to JSON and then parse
    test_data = {
        "page_access_token": os.environ["PAGE_ACCESS_TOKEN"],
        "verification_token": os.environ["VERIFICATION_TOKEN"],
        "database_configuration" : {
            "mongo_host" : "<mongo_host_ip>",
            "collections" : ["user", "transactions"]
        },
        "bot_configuration": {
            "default": {
                "type": "carousel",
                "options": [
                    {
                        "name": "log_income",
                        "target": "income_amount_prompt"
                    },
                    {
                        "name": "help",
                        "target": "help_message"
                    }
                ]
            },
            "onboarding": {
                "type": "message_list",
                "messages": [
                    {
                        "message": "Please enter your age.",
                        "expected_input": "integer",
                        "storage": "user.age"
                    }, {
                        "message": "Thanks. Have a great day!"
                    }
                ],
                "target": "placeholder_node"
            },
            "help_message": {
                "type": "message_list",
                "messages": [
                    {
                        "message": "Generic help message."
                    }
                ],
                "target": "default"
            },
            "income_amount_prompt": {
                "type": "message_list",
                "messages": [
                    {
                        "message": "How much did you earn today?",
                        "expected_input": "float",
                        "storage": "transactions.amount"
                    }
                ],
                "target": "default"
            }
        }
    }

    json_data = json.dumps(test_data)

    bot_engine = \
        Engine("sunnithan95", json_data, 
               page_access_token=test_data["page_access_token"],
               verification_token=test_data["verification_token"],
               mongo_host=test_data["database_configuration"]["mongo_host"])

    print bot_engine.process()
