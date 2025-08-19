import imaplib
import email
import re
import time
from datetime import datetime, timezone
from typing import Iterator, Optional

# Regex pattern to match 6-digit OTP codes
OTP_REGEX = re.compile(r"\b(\d{6})\b")  # adjust if OTP is not 6 digits

def _iter_message_bodies(msg: email.message.Message) -> Iterator[str]:
    """Iterate through all text/plain and text/html parts of an email message.
    
    Args:
        msg: Email message object
        
    Yields:
        str: Decoded content of each text part
    """
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                if payload:
                    yield payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            yield payload.decode(errors="ignore")

def get_latest_otp_imap(imap_host: str, 
                       username: str, 
                       password: str, 
                       email_to: str, 
                       timeout_sec: int = 90,
                       otp_regex: re.Pattern = OTP_REGEX) -> str:
    """Fetch the latest OTP code from an email using IMAP.
    
    Args:
        imap_host: IMAP server hostname (e.g., 'imap.gmail.com')
        username: Email account username
        password: Email account password or app password
        email_to: Email address to check OTP for (recipient)
        timeout_sec: Maximum time to wait for OTP email (in seconds)
        otp_regex: Regex pattern to match OTP in email body
        
    Returns:
        str: The OTP code found in the email
        
    Raises:
        TimeoutError: If no OTP is found within the timeout period
        imaplib.IMAP4.error: If there's an error connecting to the IMAP server
    """
    deadline = time.time() + timeout_sec
    since = datetime.now(timezone.utc).strftime("%d-%b-%Y")  # IMAP date format

    while time.time() < deadline:
        with imaplib.IMAP4_SSL(imap_host) as imap_conn:
            imap_conn.login(username, password)
            imap_conn.select("INBOX")
            
            # Search for unread messages since today
            status, ids = imap_conn.search(None, '(UNSEEN)', 'SINCE', since)
            if status != "OK" or not ids[0]:
                time.sleep(2)
                continue

            # Process messages from newest to oldest
            for msg_id in reversed(ids[0].split()):
                _, data = imap_conn.fetch(msg_id, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])

                # Check if the email is addressed to our target recipient
                if email_to.lower() not in ",".join(msg.get_all("To", []) or []).lower():
                    continue

                # Search for OTP in the email body
                for body in _iter_message_bodies(msg):
                    match = otp_regex.search(body)
                    if match:
                        # Mark message as read
                        imap_conn.store(msg_id, "+FLAGS", "\\Seen")
                        return match.group(1)
        
        time.sleep(3)  # Wait before next check

    raise TimeoutError(f"OTP for {email_to} not found within {timeout_sec} seconds")
