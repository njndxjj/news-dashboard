import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(recipient, subject, body):
    """Send an email notification."""
    sender_email = "your_email@example.com"
    sender_password = "your_password"  # Replace with environment variable for safety

    # Create email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    # Email body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to server and send email
        server = smtplib.SMTP('smtp.example.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Example usage
    recipient_email = "recipient@example.com"
    subject = "Daily Hotspot Summary"
    body = "Today's top articles:\n1. Title: Example Article\nSummary: This is an example summary."
    send_email(recipient_email, subject, body)