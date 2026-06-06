import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.engine import convert

app = FastAPI(title="Markify")

UPLOAD_DIR = Path("/tmp/markify")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

ALLOWED_SUFFIXES = {".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".pdf", ".txt", ".csv", ".rtf"}

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

_jobs: dict[str, dict] = {}


def _job_dir(job_id: str) -> Path:
    return UPLOAD_DIR / job_id


def _cleanup_old_jobs():
    cutoff = datetime.utcnow() - timedelta(hours=1)
    for job_id, meta in list(_jobs.items()):
        if meta.get("created_at", datetime.utcnow()) < cutoff:
            shutil.rmtree(_job_dir(job_id), ignore_errors=True)
            del _jobs[job_id]


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/convert")
async def convert_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    background_tasks.add_task(_cleanup_old_jobs)

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {suffix}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    job_id = str(uuid.uuid4())
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True)

    source_path = job_dir / file.filename
    source_path.write_bytes(content)

    result = convert(source_path, job_dir)

    if result.success:
        md_path = job_dir / f"{source_path.stem}.md"
        md_path.write_text(result.markdown, encoding="utf-8")
        _jobs[job_id] = {
            "status": "done",
            "markdown": result.markdown,
            "filename": source_path.stem,
            "created_at": datetime.utcnow(),
        }
        return JSONResponse({"job_id": job_id, "markdown": result.markdown, "status": "done"})
    else:
        _jobs[job_id] = {
            "status": "error",
            "error": result.error,
            "created_at": datetime.utcnow(),
        }
        return JSONResponse({"job_id": job_id, "status": "error", "error": result.error}, status_code=422)


@app.get("/status/{job_id}")
async def job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse({"job_id": job_id, "status": job["status"]})


@app.get("/download/{job_id}")
async def download_md(job_id: str):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Job not found or not complete")
    md_path = _job_dir(job_id) / f"{job['filename']}.md"
    return FileResponse(str(md_path), media_type="text/markdown", filename=f"{job['filename']}.md")


@app.get("/download/{job_id}/zip")
async def download_zip(job_id: str):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Job not found or not complete")
    job_dir = _job_dir(job_id)
    zip_path = job_dir / "markify_output"
    shutil.make_archive(str(zip_path), "zip", str(job_dir))
    return FileResponse(str(zip_path) + ".zip", media_type="application/zip", filename="markify_output.zip")


@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    shutil.rmtree(_job_dir(job_id), ignore_errors=True)
    _jobs.pop(job_id, None)
    return JSONResponse({"deleted": job_id})
