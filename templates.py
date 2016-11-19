"""
	Templates used for logic building.
"""
base_application_logic = \
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

webhook_logic = \
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
                state_map = state_coll.find_one({"user_id": sender_id})

                switch_node = None

                data = None

                for node, info in state_map.iteritems():
                    if node in ["flow_instantiated", "current_type", "data"]:
                        continue

                    if node["switch"]:
                        switch_node = node
                        data = info

                # we've reached the end of a message list
                flag_1 = info["index"] >= info["length"]

                flag_2 = info["length"] == 1

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

                    # flip the target switch
                    state_coll.update({"user_id": sender_id}, {
                        "$set": {
                            "%s.switch" % switch_node["target"] : True
                        }
                    }, upsert=False)

                    # send the message - this needs to be fixed by changing content folder to use a large dict
                    send_message(sender_id, content_data[switch_node["target"]])

                    continue

                curr_idx = data["index"]

                storage = data["list"][curr_idx]["storage"]

                # we assume that collections and attributes are defined with camelCase
                storage = "_".join(storage.split("."))

                target = data["list"][curr_idx]["target"]

                # store the response 
                state_coll.update({"user_id": sender_id}, {
                    "$set": {
                        "data.%s" % storage: message
                    }
                }, upsert=False)

                # increment the list index
                state_coll.find_one({"user_id": sender_id}, {
                    "$set": {
                        "%s.index" % switch_node: curr_idx + 1
                    }
                }, upsert=False)

                if (curr_idx + 1) > len(data["list"]):
                    # end of message list
                    continue

                target_content = "%s_%s" % (switch_node, curr_idx+1)

                send_message(sender_id, content_data[target_content])

                continue

            elif messaging_event["delivery"]:
                # confirm delivery - currently not supported
                pass

            elif messaging_event["optin"]:
                # confirm optin - currently not supported
                pass

            # TODO - insert data into mongo
"""

postback_logic = \
"""
if message_payload == "~payload~":
    state_coll.update({"user_id": sender_id}, {
        "$set": {
            "~target~.switch": True
        }
    }, upsert=False)

    ~data_insertion~

    send_message(sender_id, content_data["~target_content~"])

    continue
"""

content_base = \
"""
content_data = {
    ~carousels~,

    ~messages~
}
~carousels~

~messages~
"""

carousel_content_base = \
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

message_content_base = \
"""
~name~ = {
    "text": "~message_text~"
}
"""