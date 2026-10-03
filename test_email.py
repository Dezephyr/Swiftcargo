import os
import resend
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("RESEND_API_KEY")
mail_from = os.getenv("MAIL_FROM", "onboarding@resend.dev")

print("API key loaded:", "YES" if api_key else "NO")
print("API key preview:", (api_key[:8] + "..." if api_key else "(none)"))
print("Mail from:", mail_from)

# 👇 CHANGE THIS to the email you used to sign up to Resend
to_email = "uniquejoseph77@gmail.com"

if not api_key:
    raise SystemExit("❌ RESEND_API_KEY is missing from .env")

resend.api_key = api_key

print(f"\nSending test email to {to_email} ...")

try:
    result = resend.Emails.send({
        "from": mail_from,
        "to": to_email,
        "subject": "Resend test from shipment-site",
        "html": "<h1>It works 🎉</h1><p>If you got this, Resend is wired up correctly.</p>",
    })
    print("✅ Email accepted by Resend.")
    print("Response:", result)
except Exception as e:
    print("❌ Send failed.")
    print("Error type:", type(e).__name__)
    print("Error message:", e)