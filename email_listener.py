import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime, timezone
import logging
import pdf_extraction # Import the new pdf_extraction module

logger = logging.getLogger(__name__)

def connect_to_email(email_address, password, imap_server='imap.gmail.com'):
    """Connects to the IMAP server."""
    logger.info(f"Attempting to connect to email server: {imap_server}")
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        logger.info("Successfully connected to email server.")
        return mail
    except Exception as e:
        logger.error(f"Error connecting to email: {e}")
        return None

def search_emails(mail, folder='INBOX', subject_keywords=None, has_attachment=True):
    """Searches for emails based on criteria."""
    mail.select(folder)
    search_criteria = []
    if subject_keywords:
        # Build OR criteria for subject keywords
        subject_or_criteria = []
        for keyword in subject_keywords:
            subject_or_criteria.append(f'SUBJECT "{keyword}"')
        search_criteria.append(f'({" OR ".join(subject_or_criteria)})')
    
    if has_attachment:
        search_criteria.append('HAS_ATTACHMENT')

    # Combine all criteria with AND
    criteria_str = "ALL"
    if search_criteria:
        criteria_str = " ".join(search_criteria)

    logger.info(f"Searching emails in folder '{folder}' with criteria: {criteria_str}")
    status, messages = mail.search(None, criteria_str)
    message_ids = messages[0].split()
    logger.info(f"Found {len(message_ids)} relevant emails.")
    return message_ids

def download_attachments(mail, message_id, download_folder='attachments'):
    """Downloads PDF attachments from an email."""
    logger.info(f"Attempting to download attachments for email ID: {message_id.decode()}")
    status, msg_data = mail.fetch(message_id, '(RFC822)')
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject, encoding = decode_header(msg['Subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                
                filename = part.get_filename()
                if filename:
                    decoded_filename = decode_header(filename)[0][0]
                    if isinstance(decoded_filename, bytes):
                        decoded_filename = decoded_filename.decode(decode_header(filename)[0][1] or 'utf-8')

                    if decoded_filename.endswith('.pdf'):
                        filepath = os.path.join(download_folder, decoded_filename)
                        os.makedirs(download_folder, exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        logger.info(f"Downloaded PDF: {filepath}")
                        return filepath, subject, decoded_filename # Return subject and filename too
    logger.warning(f"No PDF attachment found for email ID: {message_id.decode()}")
    return None, None, None

def process_email_and_save(mail, message_id, db, PdfDocument, download_folder='attachments'):
    """Processes a single email: downloads PDF, extracts text, and saves to DB."""
    logger.info(f"Processing email ID: {message_id.decode()}")
    pdf_path, subject, filename = download_attachments(mail, message_id, download_folder)
    if pdf_path and subject and filename:
        raw_pdf_text = pdf_extraction.extract_text_from_pdf(pdf_path)
        normalized_pdf_text = pdf_extraction.normalize_text(raw_pdf_text)
        extracted_data = pdf_extraction.extract_data_from_text(normalized_pdf_text)
        
        logger.info(f"Extracted Data: {extracted_data}")
        
        # Assuming PdfDocument model is updated to accept these fields
        new_doc = PdfDocument(
            subject=subject,
            filename=filename,
            pdf_filepath=pdf_path, # Pass the PDF file path
            extracted_text=raw_pdf_text, # Still saving full raw text
            processed_at=datetime.now(timezone.utc),
            nome=extracted_data.get("nome"),
            matricula=extracted_data.get("matricula"),
            funcao=extracted_data.get("funcao"),
            empregador=extracted_data.get("empregador"),
            rg=extracted_data.get("rg"),
            cpf=extracted_data.get("cpf"),
            equipamentos=extracted_data.get("equipamentos"), # This will be a list of dicts
            data_documento=extracted_data.get("data") # Renamed to avoid conflict with 'data' keyword
        )
        db.session.add(new_doc)
        db.session.commit()
        logger.info(f"Saved document '{filename}' with subject '{subject}' to database.")
        os.remove(pdf_path) # Clean up downloaded PDF
        logger.info(f"Cleaned up downloaded PDF: {pdf_path}")
        return True
    logger.warning(f"Could not process email ID {message_id.decode()} due to missing PDF or metadata.")
    return False

def listen_and_process_emails(email_address, password, db, PdfDocument, imap_server='imap.gmail.com',
                               subject_keywords=["termo de recebimento", "termo de devolução"],
                               download_folder='attachments'):
    """Connects, listens, and processes relevant emails."""
    logger.info("Starting email listener...")
    mail = connect_to_email(email_address, password, imap_server)
    if not mail:
        logger.error("Failed to connect to email server, listener stopping.")
        return

    try:
        message_ids = search_emails(mail, subject_keywords=subject_keywords, has_attachment=True)
        if message_ids:
            logger.info(f"Found {len(message_ids)} relevant emails.")
            for msg_id in message_ids:
                success = process_email_and_save(mail, msg_id, db, PdfDocument, download_folder)
                if success:
                    logger.info(f"Successfully processed and saved email ID {msg_id.decode()}.")
                    # Mark email as seen to avoid reprocessing
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    logger.info(f"Marked email ID {msg_id.decode()} as seen.")
                else:
                    logger.warning(f"Could not process email ID {msg_id.decode()}.")
        else:
            logger.info("No new relevant emails found.")
    except Exception as e:
        logger.error(f"An error occurred during email processing: {e}")
    finally:
        if mail:
            mail.logout()
            logger.info("Email connection closed.")
        logger.info("Email listener finished.")

if __name__ == '__main__':
    # This block is for testing email_listener.py independently.
    # In the actual application, it will be called via Flask CLI.
    from dotenv import load_dotenv
    load_dotenv()

    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

    # Dummy DB and PdfDocument for standalone testing (won't actually save)
    class MockDb:
        def __init__(self):
            self.session = self
        def add(self, obj):
            print(f"Mock DB: Added {obj}")
        def commit(self):
            print("Mock DB: Committed")

    class MockPdfDocument:
        def __init__(self, subject, filename, extracted_text, processed_at):
            self.subject = subject
            self.filename = filename
            self.extracted_text = extracted_text
            self.processed_at = processed_at
        def __repr__(self):
            return f"MockPdfDocument('{self.filename}', '{self.subject}')"

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables in a .env file.")
    else:
        print("Running email listener in standalone mock mode. No data will be saved to a real database.")
        # Configure logging for standalone mode
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        listen_and_process_emails(EMAIL_ADDRESS, EMAIL_PASSWORD, MockDb(), MockPdfDocument, IMAP_SERVER)
