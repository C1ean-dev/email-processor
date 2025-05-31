# Email Processor

This project is a Flask web application that listens for emails with specific subjects, extracts PDF attachments, processes the text content of the PDFs, and saves the extracted data to a database.

## Features

- Connects to an IMAP server to listen for emails.
- Searches for emails with subjects like "termo de recebimento" or "termo de devolução".
- Downloads PDF attachments from relevant emails.
- Extracts text and structured data from PDF documents.
- Saves extracted data to a database.
- Provides a simple web interface for searching processed documents.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd email-processor
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    Create a `.env` file in the `email-processor` directory with the following variables:

    ```env
    SECRET_KEY='your_secret_key'
    DATABASE_URL='sqlite:///site.db' # Or your PostgreSQL connection string
    EMAIL_ADDRESS='your_email@gmail.com'
    EMAIL_PASSWORD='your_email_password' # Use an app password if using Gmail
    IMAP_SERVER='imap.gmail.com' # Or your IMAP server address
    ```

    *Note: For Gmail, you may need to generate an App Password if you have 2-Factor Authentication enabled.*

5.  **Initialize the database:**

    ```bash
    flask --app app init-db
    ```

6.  **Create an initial user:**

    ```bash
    flask --app app create-user
    ```

## Running the Application

1.  **Start the Flask development server:**

    ```bash
    flask --app app run --debug
    ```

    The web application will be available at `http://127.0.0.1:5000/`.

2.  **Run the email listener:**

    In a separate terminal (with the virtual environment activated), run:

    ```bash
    flask --app app run-listener
    ```

    This will start the email listener process.

## Running with Docker

To build and run the Docker image, navigate to the root of the repository (`c:/projetos/email-processor`) in your terminal.

1.  **Build the Docker image:**

    ```bash
    podman build -t email .
    # or
    # docker build -t email .
    ```

2.  **Run the Docker container:**

    ```bash
    podman run -p 8080:8080 -e SECRET_KEY='your_secret_key' -e DATABASE_URL='sqlite:///site.db' -e EMAIL_ADDRESS='your_email@gmail.com' -e EMAIL_PASSWORD='your_email_password' -e IMAP_SERVER='imap.gmail.com' email
    # or
    # docker run -p 8080:8080 -e SECRET_KEY='your_secret_key' -e DATABASE_URL='sqlite:///site.db' -e EMAIL_ADDRESS='your_email@gmail.com' -e EMAIL_PASSWORD='your_email_password' -e IMAP_SERVER='imap.gmail.com' email
    ```

    The application will be available at `http://127.0.0.1:8080/`.

## Project Structure

```
.
├── email-processor/
│   ├── __init__.py
│   ├── .env
│   ├── app.py
│   ├── auth.py
│   ├── database.py
│   ├── Dockerfile
│   ├── email_listener.py
│   ├── pdf_extraction.py
│   ├── README.md
│   ├── render.yaml
│   ├── requirements.txt
│   ├── routes.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── search.html
│   │   └── setup.html
│   └── test/
│       └── test_pdf_extraction.py
└── .gitignore
```

## Contributing

(Add contributing guidelines here)

## License

(Add license information here)
