from flask import Flask, request, jsonify, redirect, send_file
from RESTface import RESTface
from utils import reformat

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

face = RESTface()


@app.get("/favicon.ico")
def favicon():
    return redirect(
        "https://images.emojiterra.com/microsoft/fluent-emoji/15.1/3d/1f634_3d.png"
    )


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


@app.get("/<path:path>")
def get(path):
    result = face.get(path)
    if "format" in request.args:
        return reformat(result)
    return jsonify(result)


@app.post("/<path:path>")
def post(path):
    body = request.get_json(force=True, silent=True) or {}
    face.post(path, body)
    return "", 204


@app.put("/<path:path>")
def put(path):
    body = request.get_json(force=True, silent=True) or {}
    face.put(path, body)
    return "", 204


@app.delete("/<path:path>")
def delete(path):
    face.delete(path)
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
