from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
from email.header import decode_header
import imaplib


app = Flask(__name__)
CORS(app)  # Enable CORS for Android requests



def send_email(to, subject, body,Email,password):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(Email,password)
            server.sendmail(SENDER_EMAIL, to, msg.as_string())
        return {"message": "Email sent successfully!"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/send-email', methods=['POST'])
def send_email_route():
    data = request.json
    if not data or not all(k in data for k in ("to", "subject", "body","email","password")):
        return jsonify({"error": "Missing required fields"}), 400

    result = send_email(data["to"], data["subject"], data["body"],data["email"],data["password"])
    status_code = 200 if "message" in result else 500
    return jsonify(result), status_code


@app.route('/')
def welcome():
    return "Hello, World!", 200
def get_emails(email_user, email_pass):
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Fetch email IDs
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()

        email_list = []

        for num, email_id in enumerate(reversed(email_ids), start=1):  # Start numbering from 1
            # Fetch the email
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Decode subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Decode sender
                    sender, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(sender, bytes):
                        sender = sender.decode(encoding if encoding else "utf-8")

                    # Decode date
                    date = msg.get("Date")

                    # Extract email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    # Append to the list
                    email_list.append({
                        "id": str(num),
                        "subject": subject,
                        "sender": sender,
                        "body": body,
                        "date": date
                    })

        mail.logout()
        return email_list

    except Exception as e:
        return {"error": str(e)}

@app.route("/fetch-emails", methods=["POST"])
def fetch_emails():
    data = request.json
    email_user = data.get("email")
    email_pass = data.get("password")

    if not email_user or not email_pass:
        return jsonify({"error": "Missing email or password"}), 400

    emails = get_emails(email_user, email_pass)
    return jsonify(emails)
def delete_email(mail_number,user,psswd):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user,psswd)
        mail.select("inbox")

        # Fetch all email UIDs
        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()

        if not mail_ids or mail_number <= 0 or mail_number > len(mail_ids):
            return {"success": False, "message": "Invalid mail number"}

        mail_uid = mail_ids[mail_number - 1]  # Map number to email
        mail.store(mail_uid, "+FLAGS", "\\Deleted")
        mail.expunge()
        mail.logout()

        return {"success": True, "message": f"Mail {mail_number} deleted successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.route("/delete_mail", methods=["POST"])
def delete_mail():
    data = request.json
    mail_number = data.get("mail_number")
    user=data.get("user")
    psswd=data.get("password")

    if mail_number is None or user is None or psswd is None:
        return jsonify({"success": False, "message": "Mail number required or user or passwd"}), 400

    result = delete_email(mail_number,user,psswd)
    return jsonify(result)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)