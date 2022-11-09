from flask import Flask, request, jsonify

from RESTface import RESTface
from utils import reformat

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

face = RESTface()


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index(path=None):
    if path is None:
        result = face.all()
    elif path == 'favicon.ico':
        return '', 404
    else:
        body = request.get_json(force=True, silent=True) or {}
        result = face.handler({'url': path, 'body': body}, request.method)
    if 'format' in request.args:
        return reformat(result)
    return jsonify(result)
