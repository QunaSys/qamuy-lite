import argparse
import json
import pprint
import urllib.request

SERVER_URL = "http://localhost:8080/"

parser = argparse.ArgumentParser(description="Local client for sip-worker")

parser.add_argument("filename", help="path for input json.")
parser.add_argument("-e", help="only estimation", action="store_true")

args = parser.parse_args()

if __name__ == "__main__":
    method = "POST"
    headers = {"Content-Type": "application/json"}

    args = parser.parse_args()

    with open(args.filename) as f:
        data = json.load(f)
    json_data = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        SERVER_URL, data=json_data, method=method, headers=headers
    )

    with urllib.request.urlopen(request) as response:
       response_body = response.read().decode("utf-8")
    pprint.pprint(json.loads(response_body))