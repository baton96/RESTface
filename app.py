from RESTface import RESTface
from utils import reformat

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import RedirectResponse, FileResponse

app = FastAPI()

face = RESTface()


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(
        "https://images.emojiterra.com/microsoft/fluent-emoji/15.1/3d/1f634_3d.png"
    )


@app.get("/openapi.json")
async def openapi():
    return face.openapi()


@app.get("/docs")
async def docs():
    return FileResponse("docs.html")


@app.post("/upload")
async def upload(file: UploadFile):
    face.upload(file)
    return "", 204


@app.get("/")
async def get_all():
    return face.all()


@app.delete("/")
async def reset():
    face.reset()
    return "", 204


@app.get("/{path:path}")
async def get(path: str, request: Request):
    result = face.get(path)
    if "format" in request.query_params:
        return reformat(request, result)
    return result


@app.post("/{path:path}")
async def post(path: str, request: Request):
    face.post(path, await request.json())
    return "", 204


@app.put("/{path:path}")
async def put(path: str, request: Request):
    face.put(path, await request.json())
    return "", 204


@app.delete("/{path:path}")
async def delete(path: str):
    face.delete(path)
    return "", 204
