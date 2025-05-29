# Email Processor

This project aims to create a web application that listens to an email account, processes emails with specific titles and PDF attachments, extracts data from these PDFs, stores the data in a database, and provides a web interface for authenticated users to search this data.

## Features

*   **Email Listener**: Monitors an email inbox for new emails.
*   **Email Parser**: Identifies emails with "termo de recebimento" or "termo de devolução" in the subject and checks for PDF attachments.
*   **PDF Data Extraction**: Reads and extracts structured data from PDF attachments.
*   **Database Storage**: Stores extracted data for quick retrieval.
*   **User Authentication**: Secures the web interface with user login.
*   **Search Interface**: Allows authenticated users to search the extracted data.
*   **Web Application**: Built with Flask for a web-based user interface.
*   **Deployment Ready**: Configured for deployment on Fly.io.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone [repository-url]
    cd email-processor
    ```
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application**:
    ```bash
    flask run
    ```

## Configuration

*   `SECRET_KEY`: Set this environment variable for Flask's session management.
*   Email credentials and database connection strings will be configured via environment variables.

## Future Enhancements

*   Detailed PDF parsing logic based on specific document structures.
*   Robust error handling and logging for email processing.
*   Advanced search functionalities.
*   Admin interface for managing users and configurations.
