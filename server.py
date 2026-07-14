"""
Glass FM backend — implements the contract index.html already calls.
Run:  pip install -r requirements.txt && python server.py
Env:  ROOT_DIR   (default: current directory)   — the Linux directory tree exposed
      PORT       (default: 7860)                — HF Spaces expects 7860
"""
import os
import shutil
import mimetypes
from pathlib import Path

from fastapi import FastAPI, UploadFile, Form, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(os.environ.get("ROOT_DIR", ".")).resolve()
PORT = int(os.environ.get("PORT", 7860))

app = FastAPI()


# ---- path safety: every incoming path is "/"-rooted and must resolve inside ROOT_DIR ----
def safe_path(rel: str) -> Path:
    rel = rel.lstrip("/")
    p = (ROOT_DIR / rel).resolve()
    if ROOT_DIR not in p.parents and p != ROOT_DIR:
        raise HTTPException(400, "path escapes root")
    return p


def to_rel(p: Path) -> str:
    rel = p.relative_to(ROOT_DIR).as_posix()
    return "/" + rel if rel != "." else "/"


class PathBody(BaseModel):
    path: str


class FileBody(BaseModel):
    path: str
    content: str


class RenameBody(BaseModel):
    path: str
    name: str


# ---- list ----
@app.get("/api/list")
def list_dir(path: str = Query("/")):
    p = safe_path(path)
    if not p.is_dir():
        raise HTTPException(404, "not a directory")
    entries = []
    for child in sorted(p.iterdir()):
        try:
            stat = child.stat()
            entries.append({
                "name": child.name,
                "type": "dir" if child.is_dir() else "file",
                "size": None if child.is_dir() else stat.st_size,
                "mtime": None if child.is_dir() else __import__("datetime").datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
            })
        except OSError:
            continue
    return {"path": path, "entries": entries}


# ---- read file (text or raw) ----
@app.get("/api/file")
def read_file(path: str = Query(...), mode: str = Query("text")):
    p = safe_path(path)
    if not p.is_file():
        raise HTTPException(404, "not a file")
    if mode == "raw":
        media_type, _ = mimetypes.guess_type(str(p))
        return FileResponse(p, media_type=media_type or "application/octet-stream")
    try:
        return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        raise HTTPException(400, "file is not text-readable")


# ---- create / overwrite a text file ----
@app.post("/api/file")
def write_file(body: FileBody):
    p = safe_path(body.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.content, encoding="utf-8")
    return {"ok": True}


# ---- mkdir ----
@app.post("/api/mkdir")
def make_dir(body: PathBody):
    p = safe_path(body.path)
    p.mkdir(parents=True, exist_ok=True)
    return {"ok": True}


# ---- rename in place ----
@app.post("/api/rename")
def rename(body: RenameBody):
    src = safe_path(body.path)
    if not src.exists():
        raise HTTPException(404, "not found")
    dst = src.parent / body.name
    if dst.exists():
        raise HTTPException(409, "a file or folder with that name already exists")
    src.rename(dst)
    return {"ok": True}


# ---- move ----
@app.post("/api/move")
def move(body: dict):
    src = safe_path(body["from"])
    to_dir = safe_path(body["to"])
    if not src.exists():
        raise HTTPException(404, "source not found")
    to_dir.mkdir(parents=True, exist_ok=True)
    dst = to_dir / src.name
    if dst.exists():
        raise HTTPException(409, "a file or folder with that name already exists there")
    shutil.move(str(src), str(dst))
    return {"ok": True}


# ---- copy ----
@app.post("/api/copy")
def copy(body: dict):
    src = safe_path(body["from"])
    to_dir = safe_path(body["to"])
    if not src.exists():
        raise HTTPException(404, "source not found")
    to_dir.mkdir(parents=True, exist_ok=True)
    dst = to_dir / src.name
    if dst.exists():
        raise HTTPException(409, "a file or folder with that name already exists there")
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return {"ok": True}


# ---- delete ----
@app.post("/api/delete")
def delete(body: PathBody):
    p = safe_path(body.path)
    if not p.exists():
        raise HTTPException(404, "not found")
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return {"ok": True}


# ---- upload ----
@app.post("/api/upload")
async def upload(file: UploadFile, path: str = Form(...)):
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        f.write(await file.read())
    return {"ok": True}


# ---- serve the frontend itself ----
STATIC_DIR = Path(__file__).parent
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
