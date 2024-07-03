import logging
from flask import Flask, jsonify, Response, stream_with_context
from flask_restful import Api, Resource
from flask_sse import sse
from models import db, Email
import smtplib
import dns.resolver
import requests
import os
import csv
import re
from warcio.archiveiterator import ArchiveIterator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log', filemode='a')
logger = logging.getLogger()

# Common Crawl URL template
COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-MAIN-2023-06-index?url={domain}&output=json"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///emails.db')
app.config["REDIS_URL"] = "redis://localhost:6379/0"  # Ensure the Redis URL is correct
app.register_blueprint(sse, url_prefix='/stream')
db.init_app(app)
api = Api(app)

class FindEmails(Resource):
    def get(self):
        logger.info("Received request to /find_emails endpoint")
        return Response(stream_with_context(self.process_domains()), content_type='text/event-stream')

    def process_domains(self):
        csv_filename = 'domains.csv'
        
        # Ensure the CSV file exists
        if not os.path.exists(csv_filename):
            logger.error(f"{csv_filename} not found in the directory")
            yield f"data:{csv_filename} not found in the directory\n\n"
            return
        
        try:
            with open(csv_filename, mode='r', newline=None) as file:
                csv_input = csv.reader(file)
                domains = [row[0] for row in csv_input]
            logger.info(f"Read {len(domains)} domains from {csv_filename}")
            yield f"data:Read {len(domains)} domains from {csv_filename}\n\n"
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            yield f"data:Error reading CSV file: {e}\n\n"
            return

        response_emails = []
        for domain in domains:
            logger.info(f"Processing domain: {domain}")
            yield f"data:Processing domain: {domain}\n\n"
            try:
                emails = self.query_common_crawl(domain)
                logger.info(f"Found {len(emails)} emails for domain: {domain}")
                yield f"data:Found {len(emails)} emails for domain: {domain}\n\n"
                for email in emails:
                    is_valid = self.verify_email(email)
                    new_email = Email(domain=domain, email=email, valid=is_valid)
                    db.session.add(new_email)
                    db.session.commit()
                    response_emails.append({'domain': domain, 'email': email, 'valid': is_valid})
                    yield f"data:Verified email: {email}, valid: {is_valid}\n\n"
            except Exception as e:
                logger.error(f"Error processing domain {domain}: {e}")
                yield f"data:Error processing domain {domain}: {e}\n\n"

        # Write results to a new CSV file
        output_csv_filename = 'found_emails.csv'
        try:
            with open(output_csv_filename, mode='w', newline='') as output_file:
                csv_writer = csv.writer(output_file)
                csv_writer.writerow(['Domain', 'Email', 'Valid'])  # Write header
                for entry in response_emails:
                    csv_writer.writerow([entry['domain'], entry['email'], entry['valid']])
            logger.info(f"Emails successfully written to {output_csv_filename}")
            yield f"data:Emails successfully written to {output_csv_filename}\n\n"
        except Exception as e:
            logger.error(f"Error writing to CSV file: {e}")
            yield f"data:Error writing to CSV file: {e}\n\n"
            return

    # Query Common Crawl to find emails for a given domain
    def query_common_crawl(self, domain):
        logger.info(f"Querying Common Crawl for domain: {domain}")
        search_url = COMMON_CRAWL_INDEX.format(domain=domain)
        try:
            response = requests.get(search_url)
            response.raise_for_status()  # Ensure we raise an HTTPError for bad responses
            records = response.json()
            if not isinstance(records, list):
                logger.error(f"Unexpected response format for domain {domain}: {records}")
                return []

            emails = set()
            for record in records:
                warc_url = record.get('filename')
                offset = record.get('offset')
                length = record.get('length')

                if not warc_url or not offset or not length:
                    logger.error(f"Incomplete record data for domain {domain}: {record}")
                    continue

                warc_response = requests.get(f"https://commoncrawl.s3.amazonaws.com/{warc_url}", headers={'Range': f'bytes={offset}-{offset + length - 1}'})
                archive_iterator = ArchiveIterator(warc_response.raw)

                for warc_record in archive_iterator:
                    if warc_record.rec_type == 'response':
                        content = warc_record.content_stream().read().decode('utf-8')
                        emails.update(self.extract_emails(content))

            logger.info(f"Found {len(emails)} emails in Common Crawl for domain: {domain}")
            return list(emails)
        except requests.RequestException as e:
            logger.error(f"Error querying Common Crawl for domain {domain}: {e}")
            return []

    # Extract email addresses from a given text
    def extract_emails(self, text):
        email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        return set(email_pattern.findall(text))

    # Verify if an email address is valid by checking its MX records and sending a test email
    def verify_email(self, email):
        domain = email.split('@')[1]
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(records[0].exchange)
            server = smtplib.SMTP()
            server.connect(mx_record)
            server.helo('example.com')
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            if code == 250:
                return True
        except Exception as e:
            logger.error(f"Error verifying email {email}: {e}")
            return False
        return False

api.add_resource(FindEmails, '/find_emails')

if __name__ == '__main__':
    app.run(debug=True)
