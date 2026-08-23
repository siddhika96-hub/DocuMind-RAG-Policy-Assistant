from app.database import SessionLocal
from app.ingestion.pipeline import ingest_document


PDF_PATH = "sample_company_policy_plain_text.pdf"
FILENAME = "sample_company_policy_plain_text.pdf"

db = SessionLocal()

document = ingest_document(
    pdf_path=PDF_PATH,
    filename=FILENAME,
    db=db
)

print(f"Document ID: {document.id}, Status: {document.status}")

db.close()