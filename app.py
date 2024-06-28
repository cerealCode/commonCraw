from flask import Flask, jsonify
from flask_restful import Api, Resource
from models import db, Email
import smtplib
import dns.resolver
import requests
import os
import csv
from io import StringIO
import re

# Common Crawl URL template
COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-MAIN-2023-06-index?url={domain}&output=json"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///emails.db')
db.init_app(app)
api = Api(app)

class FindEmails(Resource):
    def get(self):
        # Name of the CSV file containing the domains
        csv_filename = 'domains.csv'
        
        # Ensure the CSV file exists
        if not os.path.exists(csv_filename):
            return {"message": f"{csv_filename} not found in the directory"}, 400
        
        with open(csv_filename, mode='r', newline=None) as file:
            csv_input = csv.reader(file)
            domains = [row[0] for row in csv_input]

        response_emails = []
        for domain in domains:
            emails = self.query_common_crawl(domain)
            for email in emails:
                is_valid = self.verify_email(email)
                new_email = Email(domain=domain, email=email, valid=is_valid)
                db.session.add(new_email)
                db.session.commit()
                response_emails.append({'domain': domain, 'email': email, 'valid': is_valid})

        return jsonify({'emails': response_emails})

    # Query Common Crawl to find emails for a given domain
    def query_common_crawl(self, domain):
        search_url = COMMON_CRAWL_INDEX.format(domain=domain)
        response = requests.get(search_url)
        records = response.json()

        emails = set()
        for record in records:
            warc_url = record['filename']
            offset = record['offset']
            length = record['length']

            warc_response = requests.get(f"https://commoncrawl.s3.amazonaws.com/{warc_url}", headers={'Range': f'bytes={offset}-{offset + length - 1}'})
            archive_iterator = ArchiveIterator(warc_response.raw)

            for record in archive_iterator:
                if record.rec_type == 'response':
                    content = record.content_stream().read().decode('utf-8')
                    emails.update(self.extract_emails(content))

        return list(emails)

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
            return False
        return False

api.add_resource(FindEmails, '/find_emails')

if __name__ == '__main__':
    app.run(debug=True)
