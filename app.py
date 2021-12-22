from flask import Flask, request, jsonify

from RESTface import RESTface

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

face = RESTface()


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index(path=None):
    if not path:
        result = face.all()
    elif path == 'favicon.ico':
        return '', 404
    else:
        body = request.get_json(force=True, silent=True) or {}
        result = face.handler({'url': path, 'body': body}, request.method)
    return jsonify(result)
