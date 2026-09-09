import shutil
import os
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import verify_api_key
from app.ingestion.pipeline import ingest_document
from fastapi import HTTPException,BackgroundTasks
from app.models import Document
from pydantic import BaseModel
from app.ingestion.pipeline import ingest_document, ingest_url
from app.ingestion.pipeline import process_document_background

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload",dependencies=[Depends(verify_api_key)])
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    allowed_extensions = {"pdf", "docx", "txt"}
    ext = file.filename.lower().split(".")[-1]
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Fast part: create the record, respond immediately
    document = Document(filename=file.filename, status="processing")
    db.add(document)
    db.commit()
    db.refresh(document)

    # Slow part: hand off to run AFTER this response is sent
    background_tasks.add_task(process_document_background, temp_path, file.filename, document.id)

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
    }

@router.get("/", dependencies=[Depends(verify_api_key)])
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at,
        }
        for doc in documents
    ]


@router.delete("/{document_id}",dependencies=[Depends(verify_api_key)])
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(document)
    db.commit()

    return {"message": f"Document {document_id} deleted successfully"}

class URLRequest(BaseModel):
    url: str


@router.post("/upload-url", dependencies=[Depends(verify_api_key)])
def upload_url(request: URLRequest, db: Session = Depends(get_db)):
    document = ingest_url(url=request.url, db=db)
    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
    }