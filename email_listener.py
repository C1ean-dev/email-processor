import imaplib
import email
from email.header import decode_header
import os
import re
from PyPDF2 import PdfReader
from datetime import datetime

def connect_to_email(email_address, password, imap_server='imap.gmail.com'):
    """Connects to the IMAP server."""
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        return mail
    except Exception as e:
        print(f"Error connecting to email: {e}")
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

    status, messages = mail.search(None, criteria_str)
    message_ids = messages[0].split()
    return message_ids

def download_attachments(mail, message_id, download_folder='attachments'):
    """Downloads PDF attachments from an email."""
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
                        print(f"Downloaded: {filepath}")
                        return filepath, subject, decoded_filename # Return subject and filename too
    return None, None, None

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
    return text

def process_email_and_save(mail, message_id, db, PdfDocument, download_folder='attachments'):
    """Processes a single email: downloads PDF, extracts text, and saves to DB."""
    pdf_path, subject, filename = download_attachments(mail, message_id, download_folder)
    if pdf_path and subject and filename:
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Here you would add your custom logic to separate the PDF text
        # For now, saving the entire extracted text
        
        new_doc = PdfDocument(
            subject=subject,
            filename=filename,
            extracted_text=pdf_text,
            processed_at=datetime.utcnow()
        )
        db.session.add(new_doc)
        db.session.commit()
        print(f"Saved document '{filename}' with subject '{subject}' to database.")
        os.remove(pdf_path) # Clean up downloaded PDF
        return True
    return False

def listen_and_process_emails(email_address, password, db, PdfDocument, imap_server='imap.gmail.com',
                               subject_keywords=["termo de recebimento", "termo de devolução"],
                               download_folder='attachments'):
    """Connects, listens, and processes relevant emails."""
    mail = connect_to_email(email_address, password, imap_server)
    if not mail:
        return

    print("Listening for emails...")
    try:
        message_ids = search_emails(mail, subject_keywords=subject_keywords, has_attachment=True)
        if message_ids:
            print(f"Found {len(message_ids)} relevant emails.")
            for msg_id in message_ids:
                print(f"Processing email ID: {msg_id.decode()}")
                success = process_email_and_save(mail, msg_id, db, PdfDocument, download_folder)
                if success:
                    print(f"Successfully processed and saved email ID {msg_id.decode()}.")
                    # Mark email as seen to avoid reprocessing
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                else:
                    print(f"Could not process email ID {msg_id.decode()}.")
        else:
            print("No new relevant emails found.")
    except Exception as e:
        print(f"An error occurred during email processing: {e}")
    finally:
        mail.logout()
        mail.close()

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
        listen_and_process_emails(EMAIL_ADDRESS, EMAIL_PASSWORD, MockDb(), MockPdfDocument, IMAP_SERVER)
