"""
    Engine for parsing JSON and generating control flow for chatbot webhook. 

    Thoughts/Notes
    --------------
    - how do we correctly store chat-user responses; do we ask the engine-user
    to define storage elements (e.g. db collections, objects)?
    
    - it makes most sense for message responses (i.e. user response to an
    emitted message from a list) to be stored in a database
        - the exception to this would be binary answers used to handle
        control flow
        - still haven't decided whether or not to store carousel responses 
    
    - we need an overarching unique identifier for a bot-user => used when 
    updating record attributes
    
    - we want keys/fields in JSON to be verbose
    
    - I'm (Sid) aiming to keep the deployed application as thin as possible
    with a minimal reliance on environment variables. Instead we hard-code said
    variables and pass their values as template strings. 

    - TODO: allow image url specifications for carousel options

    - current iteration supports single buttons for carousel
        - added buttons is a straight forward change on the JSON end

    - TODO: proper text templating library; simple python string formatting
    doesn't work if dictionaries are being written
        - possibly write a string templating wrapper function
        - DONE

    - (possible constraint) postbacks only trigger message lists; message lists
    can trigger message lists and postbacks

    - each user has a unique record in the state collection
        - we can use indices to keep track of when and where responses need
        to be stored for message lists
        - we need switches to know which control flow branch to follow after a
        response (e.g. postback target or message_list target)

    - how do we store intermediary decisions (e.g. carousel postback selections)
    such that we can use them for logging in the future
        - can force users to add a "data" attribute to carousel options
        - create a global "data" object which we insert into mongo at the end of
        a "flow" => easiest way to avoid updating previous transactions
        - (caveat) how do we denote the start and the end of a "flow"
        - based on the bot we built, a carousel postback following a message
        response would instantiate a flow; a message target following a carousel
        postback would terminate a flow
        - all message lists are considered flows; so we know storage for message
        lists should take place when idx == len(message_list)-1

    - for now we assume that users are dilligent in the types of responses that
    they provide
        - we only use the "expected_input" field to type cast sender responses
        before inserting into the database

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

from pymongo import MongoClient

import pdb

def format_string(string_template, **kwargs):
    """
        Helper method to perform custom string templating. Allows the inclusion
        of dictionaries in strings.

        Parameters
        ----------
        string_template : {str}
            main string to be reformatted using the new templating structure.

        kwargs : {dict}
            keyword arguments corresponding to template placeholders
    """
    template_char = '~'

    # identify all occurences of templates
    idx = 0

    templates = []

    while idx < len(string_template):
        start_idx = string_template[idx:].find(template_char)
        
        if start_idx == -1:
            # we've found all occurences of the templates
            break

        start_idx += idx

        end_idx = \
            string_template[start_idx+1:].find(template_char) + start_idx + 1 
        templates.append(string_template[start_idx:end_idx+1])
        idx = end_idx+1

    for tpl in templates:
        string_template = string_template.replace(tpl, str(kwargs[tpl[1:-1]]))

    return string_template


class Engine: 
    """
        Primary engine class for parsing JSON into application logic.
    """
    def __init__(self, user_id, page_access_token, verify_token, json_string):
        """
            Constructor. Also handles database configuration and 
            application logic instantiation.

            Parameters
            ----------
            user_id : {string}
                alphanumeric identifier for user requiring engine
            
            page_access_token : {string}
                alphanumeric token used to identify user's page; required for 
                application logic
        
            verify_token : {string}
                alphanumeric token for hub verification; required for 
                application logic       
        
            json_string : {JSON}
                data obtained from multiple sources in JSON format.
        """
        self.json_data = json.loads(json_string)
        self.pat = page_access_token
        self.vt = verify_token

        # database config
        self.client = MongoClient(os.environ["MONGO_IP"], 
                                  os.environ["MONGO_PORT"])
        self.db = self.client[user_id]

        # bot application config
        self.application_logic = self.base_application_logic()

        self.carousels = [(name, data) for name, data in self.json_data
                          if data["type"] == "carousel"]

        self.message_lists = [(name, data) for name, data in self.json_data
                              if data["type"] == "message_list"]

    def database_config(self):
        """
            Database configuration parser. Currently used to create
            database collections and insert placeholder records.

            Only reason we create collections is for safety during record
            insertions.
        """
        db_config = self.json_data["database_configuration"]

        db_config.append("state")

        for coll in db_config["collections"]:
            self.db[coll].insert({"record": "placecholder"})


    def base_application_logic(self):
        """
            Build the base for the bot's application logic. Handles app
            instantiation, verification, and basic message sending.

            For now we try our best to follow PEP8 standards. Weird indentation
            for strings is to allow for proper file writing.
        """
        base_logic = \
"""
import os
import json

import requests
from pymongo import MongoClient
from flask import Flask

from content import *

app = Flask(__name__)

# mongo constants
client = MongoClient(~mongo_ip~, ~mongo_port~)
db = client[~user_id~]
state_coll = db["state"]

# message sending helper
def send_message(sender_id, message_data):
    params = {
        "access_token": ~page_access_token~
    }

    headers = {
        "Content-Type": 'application/json'
    }

    data = json.dumps({
        "recipient": {
            "id": sender_id
        }, 
        "message": message_data
    })

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params=params, headers=headers, data=data)

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == ~verify_token~:
            return "Verificiation token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Application Verified!", 200

@app.route("/", methods=["POST"])
~webhook_logic~

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
"""

        return base_logic


    def webhook_logic(self):
        """
            Method to string together all components of the webhook logic
            (i.e. message, carousel, and quick reply handling).
        """

        web_logic = \
"""
if data["object"] == "page":
    for entry in data["entry"]:
        for messaging_event in entry["messaging"]:
            sender_id = messaging_event["sender"]["id"]

            if not db["state"].find_one({"user_id": sender_id}):
                # create a state map for the user - should only take place once
                state_coll.insert(~state_map_template~)

            if messaging_event["postback"]:
                # detect previous state to know if flow has been instantiated
                if state_coll.find_one({"user": sender_id})["current_type"] = "message_list":
                    state_coll.update({"user": sender_id}, {
                        "$set": {
                            "flow_instantiated": True
                        }
                    }, upsert=False)

                state_coll.update({"user": sender_id}, {
                    "$set": {
                        "current_type": "postback"
                    }
                }, upsert=False)

                # user submitted a postback through carousel click
                message_payload = messaging_event["postback"]["payload"]

                ~postback_control_flow~

            elif messaging_event["message"]:
                # user submitted a message response (text)
                message = messaging_event["message"]["text"]

                # set the current state to message list
                state_coll.update({"user": sender_id}, {
                    "$set": {
                        "current_type": "message_list"
                    }
                }, upsert=False)

                # find out what node has been turned on
                nodes = state_coll.find_one({"user_id": sender_id})

                switch_node = None

                for node, info in nodes.iteritems():
                    if node in ["flow_instantiated", "current_type", "data"]:
                        continue

                    if node["switch"]:
                        switch_node = node

                # we've reached the end of a message list
                flag_1 = \
                    state_coll.find_one({"user_id": sender_id})[switch_node]["index"] >= \
                    state_coll.find_one({"user_id": sender_id})[switch_node]["length"]

                # there's only one element in the message list
                flag_2 = \
                    state_coll.find_one({"user_id": sender_id})[switch_node]["length"] == 1

                flag_3 = state_coll.find_one({"user_id": sender_id})["flow_instantiated"]

                # detect the end of a flow
                if flag_1 or (flag_2 and flag_3):
                    # flip flow switch
                    state_coll.update({"user_id": sender_id}, {
                        "$set": {
                            "%s.flow_instantiated" % switch_node: False
                        }
                    }, upsert=False)

                    # reset list index
                    state_coll.update({"user_id": sender_id}, {
                        "$set": {
                            "%s.index" % switch_node: 0
                        }
                    }, upsert=False)

                    # logic to insert the state "data" record

                    # flip the node switch
                    state_coll.update({"user_id": sender_id}, {
                        "$set": {
                            "%s.switch" % switch_node: False
                        }
                    }, upsert=False)

                    # send the target message
                    send_message(sender_id, )

                ~message_control_flow~

                # detect the end of a flow based on the index and length o
                if state_coll.find_one({"user_id": sender_id})[switch_node]["index"] > 

            elif messaging_event["delivery"]:
                # confirm delivery - currently not supported
                pass

            elif messaging_event["optin"]:
                # confirm optin - currently not supported
                pass
"""
        
        # build postback flow 
        # each postback includes a payload check, a state update,
        # possible data insertion, and a message sending action
        postback_logic = \
"""
if message_payload == "~payload~":
    state_coll.find_one({"user_id": sender_id}, {
        "$set": {
            "~target~.switch": True
        }
    }, upsert=False)

    ~data_insertion~

    send_message(sender_id, ~target_content~)

    continue
"""
        
        postback_container = []

        for name, data in self.carousels:
            for option in data["options"]:
                payload = option["name"].upper()
                target = option["target"]

                # messages that follow postbacks will always be indexed at 0
                target_content = "%s_0" % option["target"] if \
                    self.json_data[option["target"]]["type"] == "message_list" \
                    else option["target"]

                if option["storage"]:
                    data_insertion = \
"""
state_coll.find_one({"user_id": sender_id}, {
    "$set": {
        "data.%s": message_payload
    }
}, upsert=False)
"""
            
                    data_insertion = data_insertion % option["storage"]
                
                else:
                    data_insertion = ""

                logic = format_string(postback_logic, 
                                      payload=option["name"].upper(),
                                      target=option["target"], 
                                      data_insertion=data_insertion,
                                      target_content=target_content)

                postback_container.append(logic)

        # handle "message" responses
        message_container = []

        message_logic = \
"""
if switch_node == ~message_list~:
    # store the response
    state_coll.find_one({"user_id": sender_id}, {
        "$set": {
            "data.~storage~": message
        }
    }, upsert=False)

    # increment the list index
"""

        return web_logic

    def content_creation(self):
        """
            Primary method for bot content creation. Outputs content to separate
            file.
        """
        # temporary standard image url
        image_url = "http://messengerdemo.parseapp.com/img/rift.png"

        carousels = [(name, data) for name, data in 
                     self.json_data["bot_configuration"].iteritems() if 
                     data["type"] == "carousel"]

        message_lists = [(name, data) for name, data in 
                         self.json_data["bot_configuration"].iteritems() if
                         data["type"] == "message_list"]

        base_content = \
"""
~carousels~

~messages~
"""

        carousel_base = \
"""
~name~ = {
    "attachment": {
        "type": "template",
        "payload": {
            "template_type": "generic",
            "elements": ~carousel_elements~
        }
    }
}
"""

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
                format_string(carousel_base, name=name, 
                              carousel_elements=car_elems))

        message_base = \
"""
~name~ = {
    "text": "~message_text~"
}
"""

        message_list_container = []

        for name, data in self.message_lists:
            # we keep message variable names as <title.index>
            for idx, msg in enumerate(data["messages"]):
                title = "%s_%s" % (name, idx)

                message_list_container.append(
                    format_string(message_base, name=title,
                                  message_text=msg["message"]))

        content = format_string(
            base_content, carousels="\n".join(carousel_container),
            messages="\n".join(message_list_container))

        # write content to file
        with open("content.py", "w") as file:
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

        for node, node_data in self.json_data.iteritems():
            if node_data["type"] != "message_list":
                continue

            state_map[node] = {
                "switch": True
            }

            # we add index and length fields
            state_map[node]["index"] = 0
            state_map[node]["length"] = len(node_data["messages"])

        state_map["flow_instantiated"] = False

        state_map["previous_type"] = ""

        state_map["data"] = {}

        return state_map

    def process(self):
        """
            Primary method to handle engine process. Calls member function in
            particular order. The end results are application and content files
            deployed and configured for the engine-user's facebook page.
        """

        self.database_config()

        self.content_creation()

        return True


if __name__ == '__main__':
    # create dict, convert to JSON and then parse
    test_data = {
        "page_access_token": os.environ["PAGE_ACCESS_TOKEN"],
        "verify_token": os.environ["VERIFY_TOKEN"],
        "database_configuration" : {
            "collections" : ["user", "transactions"]
        },
        "bot_configuration": {
            "default": {
                "type": "carousel",
                "options": [
                    {
                        "name": "log_income",
                        "target": "income_amt_prompt"
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
                ]
            },
            "income_amount_prompt": {
                "type": "message_list",
                "messages": [
                    {
                        "message": "How much did you earn today?",
                        "expected_input": "float",
                        "storage": "transactions.amount"
                    }
                ]
            }
        }
    }

    json_data = json.dumps(test_data)

    bot_engine = Engine("sunnithan95", test_data["page_access_token"], 
                        test_data["verify_token"], json_data)

    print bot_engine.process()
