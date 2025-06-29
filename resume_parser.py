import pdfplumber
import fitz  # PyMuPDF
from docx import Document
import re
import os
import logging

logger = logging.getLogger(__name__)

def extract_text(file_path, file_type):
    text = ""
    try:
        if file_type == "pdf":
            # Using PyMuPDF for better text extraction
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
        elif file_type == "docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {str(e)}")
    return text

def extract_name(text):
    # Simple heuristic to find candidate name
    name_pattern = r"^([A-Z][a-z]+(\s+[A-Z][a-z]+)+)"
    match = re.search(name_pattern, text)
    return match.group(0) if match else "Unknown"

def extract_contact_info(text):
    email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phone = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', text)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None
    }