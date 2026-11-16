# ExtractIQ

ExtractIQ is a FastAPI application that extracts searchable text, metadata, and detected information from PDF documents.

## Features

- PDF validation and text extraction
- Name, email, phone, and skills detection when present
- SQLite document history
- REST APIs for listing, viewing, and deleting documents
- Responsive browser interface
- 10 MB upload limit and corrupt-file handling

## Run locally

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

## Test

```powershell
pytest
```

The database and uploaded files are created locally and are excluded from source control.
