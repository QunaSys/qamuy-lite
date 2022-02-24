from __future__ import annotations

import base64
import json
import os

import traceback
from dataclasses import asdict, dataclass
from typing import Any, Tuple, Union

from flask import Flask, jsonify, request
from google.cloud import datastore

from .calc.calculation import calculation
from .common.job import JobResult, JobResultCalc, JobResultEst
from .common.molecule import Molecule

app = Flask(__name__)

DATASTORE_ENTITYKIND = "JobResult"
PRODUCTION_ENV = os.environ.get("PRODUCTION_ENV", False)


@app.route("/", methods=["POST"])
def entrypoint():
    req = request.get_json()

    if "message" in req:
        # From Pub/Sub
        body_json = base64.b64decode(req["message"]["data"].encode()).decode()
        body = json.loads(body_json)
    else:
        body = req

    try:
        result = jsonify(main(body))
        return result, 200
    except Exception as err:
        app.logger.error(f"Error occurs: {err}")
        app.logger.error(traceback.format_exc())
        app.logger.error(f"body: {str(body)}")
        return "{}", 204


def _store_result(job_result: JobResult):
    client = datastore.Client()
    key = client.key(DATASTORE_ENTITYKIND)  # new entity
    entity = datastore.Entity(key=key)
    entity.update(asdict(job_result))
    client.put(entity)


def _parse_input(data: dict[str, Any]) -> Tuple[str, str, Molecule, float]:
    job_id = data["job_id"]
    type = data["type"]
    input = data["input"]
    molecule = Molecule(**input["molecule"])
    tolerance = input["tolerance"]
    return job_id, type, molecule, tolerance


def main(data: dict[str, Any]) -> dict[str, Any]:
    return data
    job_id, type, molecule, tolerance = _parse_input(data)

    if type == "NISQ_ESTIMATION":
        job_result = nisq_estimation(job_id, molecule, tolerance)
    elif type == "NISQ_CALCULATION":
        job_result = nisq_calculation(job_id, molecule, tolerance)
    elif type == "FTQC_ESTIMATION":
        job_result = ftqc_estimation(job_id, molecule, tolerance)
    elif type == "CLASSICAL_ESTIMATION":
        job_result = classical_estimation(job_id, molecule, tolerance)
    else:
        job_result = JobResult(
            is_success=False, job_id=job_id, result_json='{"error": "Unknown type"}'
        )

    if PRODUCTION_ENV:
        _store_result(job_result)
    return asdict(job_result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
