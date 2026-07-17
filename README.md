# CardioTrack CT-200 Backend API

This repository contains the backend API for the Tri9T AI Internship Assignment, submitted by ANANYA U (@anu0908r).

## Features
- **PDF Ingestion**: Extracts headings, levels, and body text from medical device manuals (PDF format) and structures them hierarchically.
- **Versioning**: Preserves logical node identities across document updates using path-based matching.
- **Traceability & Selections**: Allows creating version-pinned "selections" of document nodes.
- **LLM Test Generation**: Generates QA test cases based on selected nodes.
- **Staleness Detection**: Detects if underlying document text has changed since test cases were generated and provides diff summaries.

## Tech Stack
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy (for relational tracking of nodes, versions, selections).
- **NoSQL Store**: TinyDB (a lightweight JSON store used for LLM generations, chosen to remove external dependencies like MongoDB and make local review seamless).
- **PDF Parser**: PyMuPDF (`fitz`)

## Setup & Running

### 1. Requirements
- Python 3.9+
- The required dependencies are listed in `requirements.txt` (or you can install them manually).

### 2. Installation
```bash
python -m venv venv
# On Windows
.\venv\Scripts\Activate.ps1
# On Mac/Linux
source venv/bin/activate

pip install fastapi uvicorn sqlalchemy pydantic tinydb pymupdf pytest python-multipart
```

### 3. Running the Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. You can view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

## Testing the API

### 1. Ingest Version 1
Use `curl` or Postman to upload `ct200_manual.pdf`:
```bash
curl -X POST "http://127.0.0.1:8000/documents/ingest" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "doc_name=CardioTrack" \
     -F "file=@ct200_manual.pdf"
```

### 2. List Nodes (Browse API)
```bash
curl -X GET "http://127.0.0.1:8000/nodes?doc_id=1"
```

### 3. Create a Selection
Grab a few node IDs from the output above, and submit them:
```bash
curl -X POST "http://127.0.0.1:8000/selections" \
     -H "Content-Type: application/json" \
     -d '{"name": "test-selection-1", "node_ids": [1, 2]}'
```

### 4. Generate Test Cases
```bash
curl -X POST "http://127.0.0.1:8000/selections/1/generate"
```

### 5. Ingest Version 2 (Trigger Re-ingestion Flow)
Upload `ct200_manual_v2.pdf` under the *same* document name:
```bash
curl -X POST "http://127.0.0.1:8000/documents/ingest" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "doc_name=CardioTrack" \
     -F "file=@ct200_manual_v2.pdf"
```

### 6. Check Staleness
Retrieve the generation you created earlier. It will automatically compare the original pinned nodes to the newly ingested v2 nodes and flag staleness if changes occurred.
```bash
curl -X GET "http://127.0.0.1:8000/selections/1/generations"
```

## Approach & Decisions
Please read `APPROACH.md` for my full decision log, including the reasoning behind using TinyDB and the PDF parser design choices.
