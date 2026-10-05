from flask import jsonify


def success_response(data=None, message="OK", status_code=200, meta=None):
    body = {
        "success": True,
        "message": message,
        "data": {} if data is None else data,
    }

    if meta is not None:
        body["meta"] = meta

    return jsonify(body), status_code


def error_response(message, status_code=400, code="bad_request", details=None):
    body = {
        "success": False,
        "message": message,
        "error": {
            "code": code,
            "details": details or {},
        },
    }

    return jsonify(body), status_code
