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
                       otp_regex: re.Pattern = OTP_REGEX,
                       subject_filter: str = None) -> str:
    """Fetch the latest OTP code from an email using IMAP.
    
    Args:
        imap_host: IMAP server hostname (e.g., 'imap.gmail.com')
        username: Email account username
        password: Email account password or app password
        email_to: Email address to check OTP for (recipient)
        timeout_sec: Maximum time to wait for OTP email (in seconds)
        otp_regex: Regex pattern to match OTP in email body
        subject_filter: Optional subject filter to match emails against
        
    Returns:
        str: The OTP code found in the email
        
    Raises:
        TimeoutError: If no OTP is found within the timeout period
        imaplib.IMAP4.error: If there's an error connecting to the IMAP server
    """
    deadline = time.time() + timeout_sec
    since = datetime.now(timezone.utc).strftime("%d-%b-%Y")  # IMAP date format
    print(f"Searching for OTP in emails to {email_to}" + 
          (f" with subject containing: {subject_filter}" if subject_filter else ""))

    while time.time() < deadline:
        try:
            with imaplib.IMAP4_SSL(imap_host) as imap_conn:
                imap_conn.login(username, password)
                imap_conn.select("INBOX")
                
                # Build search criteria
                search_criteria = ['UNSEEN', 'SINCE', since, 'TO', f'"{email_to}"']
                if subject_filter:
                    search_criteria.extend(['SUBJECT', f'"{subject_filter}"'])
                
                # Search for matching messages
                status, ids = imap_conn.search(None, *search_criteria)
                print(f"IMAP search status: {status}, found {len(ids[0].split()) if ids[0] else 0} messages")
                
                if status != "OK" or not ids[0]:
                    time.sleep(2)
                    continue

                # Process messages from newest to oldest
                for msg_id in reversed(ids[0].split()):
                    try:
                        _, data = imap_conn.fetch(msg_id, "(RFC822)")
                        if not data or not data[0]:
                            continue
                            
                        msg = email.message_from_bytes(data[0][1])
                        msg_subject = msg.get("Subject", "")
                        msg_to = ",".join(msg.get_all("To", []) or [])
                        print(f"Processing email - Subject: {msg_subject}, To: {msg_to}")

                        # Search for OTP in the email body
                        for body in _iter_message_bodies(msg):
                            # Print first 100 chars of the body for debugging
                            print(f"Email body preview: {body[:200]}...")
                            match = otp_regex.search(body)
                            if match:
                                otp = match.group(1)
                                print(f"Found OTP: {otp}")
                                # Mark message as read
                                imap_conn.store(msg_id, "+FLAGS", "\\Seen")
                                return otp
                    except Exception as e:
                        print(f"Error processing email: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"IMAP error: {str(e)}")
            # If there's an error, wait a bit before retrying
            time.sleep(2)
            continue
            
        time.sleep(3)  # Wait before next check
    
    # If we get here, we didn't find an OTP in time
    error_msg = f"No OTP found in emails to {email_to} within {timeout_sec} seconds"
    if subject_filter:
        error_msg += f" with subject containing: {subject_filter}"
    raise TimeoutError(error_msg)
