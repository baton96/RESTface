from flask import Flask, request, jsonify
from RESTface import handler

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
root = {}


@app.route('/<path:path>')
@app.route('/')
def index(path=None):
    if not path:
        result = root
    elif path == 'favicon.ico':
        return '', 404
    else:
        result = handler({'url': path}, request.method, root)
        if request.method == 'DELETE':
            return '', 204 if result else 404
    return jsonify(result)
