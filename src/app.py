"""
    Thin Flask server which deploys bot engine.
"""
import json

from flask import Flask, jsonify, request

from engine import Engine

# hardcoded dev database - use env var mapped to docker container
mongo_host = "mongodb://botadmin:admin@ds033015.mlab.com:33015/botengine"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def main():
    """
        Single method for instantiating and deploying bot engine.

        Parameters
        ----------
        json_config : str
            valid json configuration/specification for Messenger bot

        Returns
        -------
        tuple => web url of deployed bot application, with response status
    """
    json_config = request.args.get("json_config")

    try:
        # check for valid json string
        json_string = json.loads(json_config)
        
        # revert to string
        json_data = json.dumps(json_string)

    except:
        return "Invalid JSON", 403

    pat = request.args.get("page_access_token")

    vt = request.args.get("verification_token")

    # temporary dev user until multiple mongo databases are used
    bot_engine = Engine("dev", json_data, page_access_token=pat,
                        verification_token=vt, mongo_host=mongo_host)

    bot_engine.process()

    return web_url, 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
