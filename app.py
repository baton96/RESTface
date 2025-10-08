from flask import Flask, request, jsonify, redirect, send_file
from RESTface import RESTface
from utils import reformat

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

face = RESTface()


@app.get("/favicon.ico")
def favicon():
    favicon_url = (
        "https://images.emojiterra.com/microsoft/fluent-emoji/15.1/3d/1f634_3d.png"
    )
    return redirect(favicon_url)


@app.get("/openapi.json")
def openapi():
    return jsonify(face.openapi())


@app.get("/docs")
def docs():
    return send_file("docs.html")


@app.get("/")
def get_all():
    return jsonify(face.all())


@app.post("/")
def receive_file():
    face.receive_file(request)
    return "", 204


@app.delete("/")
def reset():
    face.reset()
    return "", 204


@app.route("/<path:path>", methods=["POST", "PUT", "DELETE"])
def index(path):
    body = request.get_json(force=True, silent=True) or {}
    result = face.handler({"url": path, "body": body}, request.method)
    if request.method == "DELETE":
        return "", 204
    if "format" in request.args:
        return reformat(result)
    return jsonify(result)


@app.get("/<path:path>")
def get(path):
    result = face.get({"url": path})
    if "format" in request.args:
        return reformat(result)
    return jsonify(result)


@app.post("/<path:path>")
@app.put("/<path:path>")
def upsert(path):
    face.upsert({"url": path}, request.method)
    return "", 204


# @app.route('/upload', methods=['GET', 'POST', 'PUT', 'DELETE'])
def upload():
    if request.method == "GET":
        return """
            <form method=post enctype=multipart/form-data>
                <input type=file name=file123 multiple>
                <input type=submit value=Upload>
            </form>
        """
    else:
        if request.files:
            file = next(iter(request.files.values()))
            print(file.stream.read().decode("utf-8"))
            print(file.filename)
        return "OK"
