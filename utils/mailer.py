import resend
from flask import current_app


def send_tracking_email(to_email, recipient_name, sender_name, tracking_id, origin, destination):
    """Send the tracking ID email. Returns (success: bool, message: str)."""
    api_key = current_app.config.get("RESEND_API_KEY")
    mail_from = current_app.config.get("MAIL_FROM", "onboarding@resend.dev")

    if not api_key:
        return False, "RESEND_API_KEY is not set."

    resend.api_key = api_key

    subject = f"Your shipment is on the way — {tracking_id}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: auto; padding: 24px; color: #0f172a;">
      <h2 style="color: #2563eb;">Your shipment has been created</h2>
      <p>Hi {recipient_name},</p>
      <p><strong>{sender_name}</strong> has sent you a package.</p>
      <p style="margin: 20px 0;">
        <strong>Tracking ID:</strong>
        <span style="font-family: monospace; background: #f1f5f9; padding: 4px 8px; border-radius: 4px;">
          {tracking_id}
        </span>
      </p>
      <p><strong>Route:</strong> {origin} → {destination}</p>
      <p style="margin-top: 24px;">You can track your package anytime by visiting our site and entering the tracking ID above.</p>
      <p style="color: #64748b; font-size: 13px; margin-top: 32px;">— Shipment Tracker</p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": mail_from,
            "to": to_email,
            "subject": subject,
            "html": html,
        })
        return True, "Email sent."
    except Exception as e:
        return False, str(e)