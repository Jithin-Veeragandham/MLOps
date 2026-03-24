import base64
import json
import os
import urllib.request

def notify(event, context):
    message = base64.b64decode(event["data"]).decode("utf-8")
    data = json.loads(message)

    status = data.get("status", "UNKNOWN")
    stage = data.get("stage", "unknown")
    reason = data.get("reason", "No details provided.")

    emoji = "✅" if status == "SUCCESS" else "❌"
    subject = f"ML Pipeline {status} at stage: {stage}"
    body = f"{emoji} ML Pipeline {status}\n\nStage: {stage}\nDetails: {reason}"

    sendgrid_payload = {
        "personalizations": [
            {
                "to": [{"email": os.environ["ALERT_EMAIL"]}],
                "subject": subject
            }
        ],
        "from": {"email": os.environ["SENDER_EMAIL"]},
        "content": [{"type": "text/plain", "value": body}]
    }

    api_key = os.environ["SENDGRID_API_KEY"].strip()
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(sendgrid_payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        print(f"SendGrid response: {response.status}")