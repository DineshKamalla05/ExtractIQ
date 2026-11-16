import re
import uuid
from pathlib import Path

import pymupdf as fitz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from app.database import (
    create_database,
    delete_document,
    get_document,
    list_documents,
    save_document,
)

app = FastAPI(title="ExtractIQ", version="1.0.0")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = PROJECT_ROOT / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024

create_database()


def extract_information(text: str):
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = next(
        (line for line in lines[:5] if "@" not in line and not re.search(r"\d", line)),
        None,
    )
    skill_list = [
        "Python", "Java", "C", "C++", "C#", "HTML", "CSS", "JavaScript",
        "TypeScript", "React", "Node.js", "SQL", "FastAPI", "Flask",
        "Django", "Tableau", "Power BI", "Git", "Docker", "AWS", "MongoDB",
    ]
    found_skills = [
        skill for skill in skill_list
        if re.search(r"\b" + re.escape(skill).replace(r"\ ", r"\s+") + r"\b",
                     text, re.IGNORECASE)
    ]
    return {
        "name": name,
        "email": email_match.group() if email_match else None,
        "phone": re.sub(r"\s+", " ", phone_match.group()).strip()
        if phone_match else None,
        "skills": found_skills,
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    original_filename = file.filename or ""
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="PDF must be smaller than 10 MB")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF")

    stored_filename = f"{uuid.uuid4()}.pdf"
    file_path = UPLOAD_FOLDER / stored_filename
    try:
        file_path.write_bytes(content)
        with fitz.open(stream=content, filetype="pdf") as document:
            page_count = len(document)
            pdf_metadata = document.metadata
            extracted_text = "\n".join(page.get_text() for page in document).strip()
    except (OSError, fitz.FileDataError) as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not read the PDF") from error

    information = extract_information(extracted_text)
    document_id = save_document(
        original_filename, page_count, extracted_text, information, stored_filename
    )
    return {
        "id": document_id,
        "filename": original_filename,
        "page_count": page_count,
        "metadata": pdf_metadata,
        "extracted_text": extracted_text,
        "extracted_information": information,
        "database_status": "Document saved successfully",
    }


@app.get("/documents")
def documents():
    return {"documents": list_documents()}


@app.get("/documents/{document_id}")
def document(document_id: int):
    result = get_document(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@app.delete("/documents/{document_id}")
def remove_document(document_id: int):
    result = get_document(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    deleted = delete_document(document_id)
    if result.get("stored_filename"):
        (UPLOAD_FOLDER / result["stored_filename"]).unlink(missing_ok=True)
    return {"deleted": deleted, "id": document_id}


app.mount("/", StaticFiles(directory=PROJECT_ROOT / "frontend", html=True), name="frontend")
