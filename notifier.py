import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from models import Listing

logger = logging.getLogger(__name__)


def send_notification(listings: list[Listing], config: dict) -> None:
    if not listings:
        return

    email_cfg = config["email"]
    n = len(listings)
    boats = config.get("boats", [{"name": "Olson 911SE"}])
    boat_names = ", ".join(b["name"] for b in boats)
    subject = f"[BoatListings] {n} new {boat_names} listing{'s' if n != 1 else ''} found"

    html_body = _build_html(listings, boat_names)
    text_body = _build_text(listings, boat_names)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_cfg["from_addr"]
    msg["To"] = ", ".join(email_cfg["to_addrs"])
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as server:
            server.starttls()
            server.login(email_cfg["smtp_user"], email_cfg["smtp_password"])
            server.sendmail(
                email_cfg["from_addr"],
                email_cfg["to_addrs"],
                msg.as_string(),
            )
        logger.info(f"Email sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise


def _build_html(listings: list[Listing], boat_names: str = "Olson 911SE") -> str:
    rows = ""
    for l in listings:
        rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 12px;">
                <a href="{l.url}" style="color: #1a73e8; font-size: 16px; font-weight: bold; text-decoration: none;">{l.title}</a>
                <div style="color: #555; margin-top: 4px;">
                    {f'<strong>{l.price}</strong>' if l.price else ''}
                    {f' &mdash; {l.location}' if l.location else ''}
                </div>
                <div style="color: #888; font-size: 12px; margin-top: 4px;">
                    Source: {l.source}
                    {f'<br>{l.description[:150]}...' if l.description and len(l.description) > 10 else ''}
                </div>
            </td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">New {boat_names} Listings</h2>
        <table style="width: 100%; border-collapse: collapse;">
            {rows}
        </table>
        <p style="color: #999; font-size: 12px; margin-top: 24px;">
            Sent by OlsonListings monitor
        </p>
    </body>
    </html>"""


def _build_text(listings: list[Listing], boat_names: str = "Olson 911SE") -> str:
    lines = [f"New {boat_names} Listings", "=" * 30, ""]
    for l in listings:
        lines.append(f"{l.title}")
        if l.price or l.location:
            lines.append(f"  {l.price or ''} {l.location or ''}".strip())
        lines.append(f"  {l.url}")
        lines.append(f"  Source: {l.source}")
        lines.append("")
    return "\n".join(lines)
