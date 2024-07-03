
# Detailed Guide to Running the Flask Email Finder Application

## Overview

This Flask application is designed to find and verify email addresses from domains listed in a CSV file using the Common Crawl data. The application uses Flask, Flask-RESTful, and Flask-SSE for handling server-sent events, and SQLAlchemy for database interactions. Redis is used for managing server-sent events. Logging is configured to capture application activity.

## Prerequisites

Before running the application, ensure you have the following installed on your system:

- Python 3.7 or later
- Flask
- Flask-RESTful
- Flask-SSE
- SQLAlchemy
- Redis
- smtplib
- dnspython
- requests
- warcio

## Installation

### Step 1: Clone the Repository

Clone the repository from GitHub:

```sh
git clone <repository_url>
cd <repository_directory>
```

### Step 2: Create and Activate a Virtual Environment

It is recommended to create a virtual environment to manage dependencies:

```sh
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Step 3: Install Dependencies

Install the required Python packages:

```sh
pip install -r requirements.txt
```

### Step 4: Set Up Redis Server

Ensure Redis is installed and running on your system. The application expects Redis to be running on `localhost` at port `6379`.

To install Redis, follow the instructions on the [Redis website](https://redis.io/download).

## Configuration

### Step 1: Database Configuration

Set up your database. By default, the application uses SQLite, but you can configure it to use any other SQL database by setting the `DATABASE_URL` environment variable.

### Step 2: Create the Database

Run the following commands to create the database:

```sh
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
```

### Step 3: Environment Variables

Set the necessary environment variables. You can create a `.env` file in the project root with the following content:

```sh
DATABASE_URL=sqlite:///emails.db
REDIS_URL=redis://localhost:6379/0
```

## Running the Application

### Step 1: Start the Redis Server

Ensure the Redis server is running:

```sh
redis-server
```

### Step 2: Run the Flask Application

Start the Flask application:

```sh
flask run
```

The application should now be running on `http://localhost:5000`.

## Usage

### Endpoint: `/find_emails`

This endpoint processes the domains listed in `domains.csv` and finds email addresses associated with those domains.

#### Prerequisites

1. **Create a CSV file named `domains.csv`** in the project directory containing the list of domains you want to process. The file should have one domain per line.

2. **Start the Redis Server**

   Ensure the Redis server is running:

   ```sh
   redis-server
   ```

#### Sending a GET Request

To process the domains and find emails, send a GET request to the `/find_emails` endpoint. You can use `curl` for this:

```sh
curl http://localhost:5000/find_emails
```

#### Streaming Updates

The application streams real-time updates as it processes each domain. You can see the following types of messages in the stream:

- **Reading Domains**: `Read N domains from domains.csv`
- **Processing Domain**: `Processing domain: example.com`
- **Found Emails**: `Found N emails for domain: example.com`
- **Verified Email**: `Verified email: email@example.com, valid: True/False`
- **Errors**: Descriptive error messages if any issues occur

#### Output

The results, including the validity of each email, are saved in `found_emails.csv` in the project directory. The log file `app.log` captures detailed information about the application's operations.

#### Example

Below is an example of how to structure your `domains.csv` file and an example output from the `found_emails.csv` file:

##### `domains.csv`

```csv
example.com
anotherdomain.com
```

##### `found_emails.csv`

```csv
Domain,Email,Valid
example.com,email1@example.com,True
example.com,email2@example.com,False
anotherdomain.com,email3@anotherdomain.com,True
```

### Logs

Logs are written to `app.log` in the project directory, capturing detailed information about the application's operations. This includes reading domains, processing domains, finding and verifying emails, and any errors encountered.

### Further Actions

1. **Check the `found_emails.csv` file** for the results.
2. **Refer to `app.log`** for detailed logs and troubleshooting.

### Stopping the Application

To stop the application, you can use `Ctrl+C` in the terminal where the Flask server is running. Also, stop the Redis server if it is running separately.

By following these instructions, you should be able to run and use the Flask Email Finder application effectively.
