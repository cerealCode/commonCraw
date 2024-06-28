# Email Finder and Verifier API - Local Setup

## Description
This project is a production-level API for finding and verifying email addresses similar to Hunter.io. The application is built using Flask and can be run locally.

## Project Structure
- `app.py`: Main application file containing the API endpoints.
- `models.py`: Database models using SQLAlchemy.
- `init_db.py`: Script to initialize the database.
- `requirements.txt`: List of Python dependencies.
- `Procfile`: Configuration for Heroku deployment (not needed for local setup).
- `README_local.md`: Instructions for local setup and usage.

## Local Setup

### Prerequisites
- Python 3 installed on your machine
- Pip (Python package installer) installed

### Step 1: Set Up a Virtual Environment
1. Open a terminal and navigate to the directory where you extracted the project.
2. Create a virtual environment:
    ```sh
    python3 -m venv env
    ```
3. Activate the virtual environment:
    - On Windows:
        ```sh
        .\env\Scripts\activate
        ```
    - On macOS and Linux:
        ```sh
        source env/bin/activate
        ```

### Step 2: Install Dependencies
1. Install the required libraries:
    ```sh
    pip install -r requirements.txt
    ```

### Step 3: Initialize the Database
1. Initialize the SQLite database:
    ```sh
    python init_db.py
    ```

### Step 4: Run the Application
1. Start the Flask application:
    ```sh
    python app.py
    ```

2. The application should now be running at `http://localhost:5000`.

### Usage

1. **Endpoint to Find Emails:**
   - URL: `/find_emails`
   - Method: `POST`
   - Payload: `multipart/form-data` with a CSV file containing domains
   - Example:
     ```sh
     curl -X POST -F "file=@domains.csv" http://localhost:5000/find_emails
     ```

2. **CSV File Format:**
   - The CSV file should have a single column with each row containing a domain name.
   - Example:
     ```
     example.com
     anotherdomain.com
     ```

## Note
- Ensure your CSV file is properly formatted and only contains domain names.
- The API will scrape and verify emails for each domain in the CSV file.
