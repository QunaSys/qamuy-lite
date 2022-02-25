from __future__ import annotations

import os

import traceback
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)

PRODUCTION_ENV = os.environ.get("PRODUCTION_ENV", False)


@app.route("/", methods=["GET"])
def hello():
    return "Hello", 200


@app.route("/exec", methods=["POST"])
def exec():
    req = request.get_json()
    body = req

    try:
        result = jsonify(main(body))
        return result, 200
    except Exception as err:
        app.logger.error(f"Error occurs: {err}")
        app.logger.error(traceback.format_exc())
        app.logger.error(f"body: {str(body)}")
        return "{}", 204


def main(data: dict[str, Any]) -> dict[str, Any]:
    return data


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
