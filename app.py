# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import signal
import sys
from types import FrameType

from flask import Flask, jsonify
from pymongo import MongoClient
import os

from utils.logging import logger

app = Flask(__name__)


@app.route("/")
def hello() -> str:
    # Use basic logging with custom fields
    logger.info(logField="custom-entry", arbitraryField="custom-entry")

    # https://cloud.google.com/run/docs/logging#correlate-logs
    logger.info("Child logger with trace Id.")

    return "Hello, World!"


@app.route("/test")
def test() -> str:
    # Use basic logging with custom fields
    logger.info(logField="custom-entry", arbitraryField="custom-entry")

    # https://cloud.google.com/run/docs/logging#correlate-logs
    logger.info("Child logger with trace Id.")

    return "GCR Test!"


@app.route("/mongo-test")
def mongo_test():
    """
    Connects to a MongoDB Atlas cluster using the MONGODB_URI environment variable,
    fetches the first document from the 'test' database and 'test' collection,
    and returns it as JSON.
    """
    mongo_uri = "mongodb+srv://dev:57xg9ejuOLw7aSFP@laserdatacluster.dihytwb.mongodb.net/?retryWrites=true&w=majority&appName=laserDataCluster"
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set.")
        return jsonify({"error": "MONGODB_URI environment variable not set."}), 500

    try:
        client = MongoClient(mongo_uri)
        db = client.get_database("laserUser")
        collection = db.get_collection("users")
        doc = collection.find_one()
        client.close()
        if doc:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for JSON serialization
        return jsonify(doc if doc else {"message": "No documents found."})
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return jsonify({"error": str(e)}), 500


def shutdown_handler(signal_int: int, frame: FrameType) -> None:
    logger.info(f"Caught Signal {signal.strsignal(signal_int)}")

    from utils.logging import flush

    flush()

    # Safely exit program
    sys.exit(0)


if __name__ == "__main__":
    # Running application locally, outside of a Google Cloud Environment

    # handles Ctrl-C termination
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host="localhost", port=8080, debug=True)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)
