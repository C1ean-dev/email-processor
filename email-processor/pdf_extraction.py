import os
import re
import logging
import subprocess
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import unicodedata

logger = logging.getLogger(__name__)

# Explicitly set Tesseract and Poppler paths if they are not in system PATH
# These paths are based on common Windows installations.
# For Linux/Render, Tesseract and Poppler are usually in system PATH by default.
# If running on Linux, these lines might not be strictly necessary but won't hurt.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Add Poppler's bin directory to the PATH for pdf2image
poppler_path = r'C:\poppler\Library\bin'
if os.path.exists(poppler_path) and poppler_path not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + poppler_path
    logger.info(f"Added Poppler path to environment PATH: {poppler_path}")


def check_tesseract_installed():
    """Checks if Tesseract OCR is installed and accessible."""
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR is installed and accessible.")
        return True
    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract OCR is not found. Please install it and ensure it's in your system's PATH, or set pytesseract.pytesseract.tesseract_cmd correctly.")
        return False
    except Exception as e:
        logger.warning(f"Error checking Tesseract installation: {e}")
        return False

def check_poppler_installed():
    """Checks if Poppler (pdftoppm) is installed and accessible."""
    try:
        subprocess.run(['pdftoppm', '-v'], check=True, capture_output=True, text=True)
        logger.info("Poppler (pdftoppm) is installed and accessible.")
        return True
    except FileNotFoundError:
        logger.warning("Poppler (pdftoppm) is not found. Please install it and ensure its 'bin' directory is in your system's PATH.")
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(f"Poppler (pdftoppm) command failed: {e}. Please check your Poppler installation.")
        return False
    except Exception as e:
        logger.warning(f"Error checking Poppler installation: {e}")
        return False

def normalize_text(text):
    """Converts text to lowercase and removes accents, preserving hyphens."""
    normalized_text = unicodedata.normalize('NFD', text)
    normalized_text = normalized_text.encode('ascii', 'ignore').decode('utf-8').lower()
    return normalized_text

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using OCR if direct extraction fails."""
    logger.info(f"Attempting to extract text from PDF: {pdf_path}")
    text = ""
    try:
        from PyPDF2 import PdfReader
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        
        if text.strip():
            logger.info(f"Successfully extracted text directly from PDF: {pdf_path}")
            return text
        else:
            logger.info(f"No direct text extracted from {pdf_path}, attempting OCR.")

    except Exception as e:
        logger.warning(f"Direct text extraction failed for {pdf_path}: {e}. Attempting OCR.")
    
    try:
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            logger.info(f"Performing OCR on page {i+1} of {pdf_path}")
            page_text = pytesseract.image_to_string(image, lang='por')
            text += page_text + "\n"
        logger.info(f"Successfully extracted text from PDF using OCR: {pdf_path}")
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path} using OCR: {e}. Make sure Tesseract and Poppler are installed and configured correctly.")
    return text

def extract_data_from_text(text):
    """Extracts specific data points from the given text."""
    data = {
        "nome": None,
        "matricula": None,
        "funcao": None,
        "empregador": None,
        "rg": None,
        "cpf": None,
        "equipamentos": [],
        "data": None
    }

    # Use the user-provided logic for extraction
    # Nome
    nome_match = re.search(r"empregado:\s*(.*?)\s*matricula:", text, re.DOTALL)
    if nome_match:
        data["nome"] = nome_match.group(1).strip()

    # Matricula
    matricula_match = re.search(r"matricula:\s*(.*?)\s*funcao:", text, re.DOTALL)
    if matricula_match:
        data["matricula"] = matricula_match.group(1).strip()

    # Função
    funcao_match = re.search(r"funcao:\s*(.*?)\s*r\.g\. n(?:º|°)?:", text, re.DOTALL)
    if funcao_match:
        data["funcao"] = funcao_match.group(1).strip()

    # RG
    rg_match = re.search(r"r\.g\. n(?:º|°)?:(?:\s*nº:)?\s*(.*?)\s*empregador:", text, re.DOTALL)
    if rg_match:
        data["rg"] = rg_match.group(1).strip()

    # Empregador
    empregador_match = re.search(r"empregador:\s*(.*?)\s*cpf:", text, re.DOTALL)
    if empregador_match:
        data["empregador"] = empregador_match.group(1).strip()

    # CPF - Adjusted to be more precise and stop before the junk text
    cpf_match = re.search(r"cpf:\s*([\d\.\-]{11,14}|)", text, re.DOTALL)
    if cpf_match:
        data["cpf"] = cpf_match.group(1).strip()
        if not data["cpf"]:
            data["cpf"] = ""

    # Equipamentos - Refined based on new user feedback
    equipamentos_block_match = re.search(r"ferramentas:\s*(.*?)\s*declaro", text, re.DOTALL)
    if equipamentos_block_match:
        equipamentos_block = equipamentos_block_match.group(1).strip()
        
        for line in equipamentos_block.split('\n'):
            line = line.strip()
            if not line:
                continue

            equipment_name = line
            imei = None
            patrimonio = None

            imei_match = re.search(r"imei:\s*(\S+)", equipment_name, re.IGNORECASE)
            if imei_match:
                imei = imei_match.group(1).strip()
                equipment_name = re.sub(r"imei:\s*\S+", "", equipment_name, flags=re.IGNORECASE).strip()

            patrimonio_match = re.search(r"patrimonio:\s*(\S+)", equipment_name, re.IGNORECASE)
            if patrimonio_match:
                patrimonio = patrimonio_match.group(1).strip()
                equipment_name = re.sub(r"patrimonio:\s*\S+", "", equipment_name, flags=re.IGNORECASE).strip()
            
            equipment_name = re.sub(r"^equipamento:\s*", "", equipment_name, flags=re.IGNORECASE).strip()

            if equipment_name:
                equipment_info = {"nome_equipamento": equipment_name}
                if imei:
                    equipment_info["imei"] = imei
                if patrimonio:
                    equipment_info["patrimonio"] = patrimonio
                data["equipamentos"].append(equipment_info)

    # Date
    date_match = re.search(r"sao paulo,\s*(\d{1,2})\s*de\s*([a-zçãõáéíóúàèìòùâêîôûäëïöüñ]+)\s*de\s*(\d{4})", text)
    if date_match:
        day = date_match.group(1)
        month_name = date_match.group(2)
        year = date_match.group(3)
        
        month_mapping = {
            "janeiro": "01", "fevereiro": "02", "marco": "03", "abril": "04", "maio": "05", "junho": "06",
            "julho": "07", "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
        }
        month = month_mapping.get(month_name, "00")
        if month != "00":
            data["data"] = f"{day}/{month}/{year}"
        else:
            logger.warning(f"Could not parse month name: {month_name}")

    return data
