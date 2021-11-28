from flask import Flask, request, jsonify
from RESTface import handler

app = Flask(__name__)
root = {}


@app.route('/<path:path>')
@app.route('/')
def index(path=None):
    if not path:
        result = root
    else:
        result = handler({'url': path}, request.method, root)
    return jsonify(result)
