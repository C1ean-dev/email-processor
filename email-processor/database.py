from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB # Import JSONB for PostgreSQL specific type
from datetime import datetime, timezone
import json # For serializing/deserializing JSON data

db = SQLAlchemy()

class PdfDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    pdf_filepath = db.Column(db.String(512), nullable=True) # New column for PDF file path
    extracted_text = db.Column(db.Text, nullable=True) # Raw extracted text
    processed_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Extracted structured data fields
    nome = db.Column(db.String(255), nullable=True)
    matricula = db.Column(db.String(255), nullable=True)
    funcao = db.Column(db.String(255), nullable=True)
    empregador = db.Column(db.String(255), nullable=True)
    rg = db.Column(db.String(255), nullable=True)
    cpf = db.Column(db.String(255), nullable=True)
    
    # Equipamentos: Store as JSONB for PostgreSQL, or Text for generic DBs
    # If using PostgreSQL, uncomment the line below and comment out the db.Text line
    # equipamentos = db.Column(JSONB, nullable=True)
    equipamentos = db.Column(db.Text, nullable=True) # Storing as JSON string for broader compatibility

    data_documento = db.Column(db.String(10), nullable=True) # Storing date as string "DD/MM/YYYY"

    def __repr__(self):
        return f"<PdfDocument {self.filename} - {self.subject}>"

    def __init__(self, subject, filename, extracted_text, processed_at,
                 nome=None, matricula=None, funcao=None, empregador=None,
                 rg=None, cpf=None, equipamentos=None, data_documento=None,
                 pdf_filepath=None): # Added pdf_filepath to init
        self.subject = subject
        self.filename = filename
        self.extracted_text = extracted_text
        self.processed_at = processed_at
        self.nome = nome
        self.matricula = matricula
        self.funcao = funcao
        self.empregador = empregador
        self.rg = rg
        self.cpf = cpf
        self.equipamentos = json.dumps(equipamentos) if equipamentos is not None else None
        self.data_documento = data_documento
        self.pdf_filepath = pdf_filepath # Assign new field

    # Method to deserialize equipments when retrieving from DB (optional, can be done in application logic)
    @property
    def equipamentos_list(self):
        if self.equipamentos:
            return json.loads(self.equipamentos)
        return []

# Note: You will need to run Flask database migrations (e.g., using Flask-Migrate)
# to apply these schema changes to your PostgreSQL database.
