import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

port = 465
password = ""
sender = ""

def send_email(receiver, subject, html):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver
    message.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())

def build_html(event, event_time, health_checker):
    return f"""
<html>
<body>
<b>Event Type:</b> {event}<br>
<b>Event Time:</b> {event_time}<br>
<b>Server:</b> {health_checker.host.host}<br>
<b>Port:</b> {health_checker.host.port}<br>
<b>Threshold:</b> Health: {health_checker.threshold.health}/ Unhealthy: {health_checker.threshold.unhealthy}<br>
<b>Inverval:</b> {health_checker.interval}<br>
</body>
</html>
"""
