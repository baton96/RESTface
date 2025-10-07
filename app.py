from flask import Flask, request, jsonify, redirect

from RESTface import RESTface
from utils import reformat, receive_file

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

face = RESTface()


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/", methods=["GET", "POST", "PUT", "DELETE"])
def index(path=None):
    if request.files:
        receive_file()
    if path is None:
        result = face.all()
    elif path == "favicon.ico":
        return redirect(
            "https://images.emojiterra.com/microsoft/fluent-emoji/15.1/3d/1f634_3d.png"
        )
    else:
        body = request.get_json(force=True, silent=True) or {}
        result = face.handler({"url": path, "body": body}, request.method)
    if "format" in request.args:
        return reformat(result)
    return jsonify(result)


# @app.route('/upload', methods=['GET', 'POST', 'PUT', 'DELETE'])
def upload():
    if request.method == "GET":
        return """
            <form method=post enctype=multipart/form-data>
                <input type=file name=file123 multiple>
                <input type=submit value=Upload>
            </form>"""
    else:
        if request.files:
            file = next(iter(request.files.values()))
            print(file.stream.read().decode("utf-8"))
            print(file.filename)
        return "OK"
