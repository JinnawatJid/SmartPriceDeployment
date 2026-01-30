#!/usr/bin/env python3
"""
Email Reply Checker Service
ตรวจสอบ email inbox และอัปเดตสถานะการอนุมัติ/ปฏิเสธ
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
from typing import Optional, Tuple

from config.email_config import (
    IMAP_SERVER,
    IMAP_PORT,
    EMAIL_ADDRESS,
    EMAIL_PASSWORD
)
from special_price_request.service import approve_request, reject_request, get_request_detail


def decode_email_subject(subject: str) -> str:
    """Decode email subject"""
    decoded_parts = decode_header(subject)
    decoded_subject = ""
    
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_subject += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            decoded_subject += part
    
    return decoded_subject


def extract_request_number(subject: str) -> Optional[str]:
    """
    Extract request number from email subject
    Format: [Approve Required] Special Price Request SP-250130-0001
    """
    match = re.search(r'SP-\d{6}-\d{4}', subject)
    if match:
        return match.group(0)
    return None


def check_approval_decision(body: str) -> Optional[Tuple[str, str]]:
    """
    Check if email body contains APPROVE or REJECT
    Returns: (decision, reason) or None
    """
    body_upper = body.upper()
    
    # Check for APPROVE
    if 'APPROVE' in body_upper:
        return ('approve', '')
    
    # Check for REJECT with reason
    if 'REJECT' in body_upper:
        # Try to extract reason after REJECT
        lines = body.split('\n')
        for i, line in enumerate(lines):
            if 'REJECT' in line.upper():
                # Get next line as reason
                if i + 1 < len(lines):
                    reason = lines[i + 1].strip()
                    if reason and not reason.startswith('***'):
                        return ('reject', reason)
                return ('reject', 'ไม่ระบุเหตุผล')
    
    return None


def get_email_body(msg) -> str:
    """Extract email body from message"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    
    return body


def extract_pdf_attachments(msg, request_number: str) -> list:
    """
    Extract PDF attachments from email and save them
    Returns: list of saved file paths
    """
    from pathlib import Path
    from config.email_config import PDF_STORAGE_PATH
    
    saved_files = []
    
    print(f"   🔍 Checking for PDF attachments...")
    print(f"   📁 PDF storage path: {PDF_STORAGE_PATH}")
    
    # Ensure directory exists
    PDF_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    
    if msg.is_multipart():
        attachment_count = 0
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            content_type = part.get_content_type()
            
            print(f"   📎 Part: type={content_type}, disposition={content_disposition[:50]}")
            
            # Check if this is an attachment
            if "attachment" in content_disposition:
                attachment_count += 1
                filename = part.get_filename()
                
                print(f"   📎 Found attachment #{attachment_count}: {filename}")
                
                if filename and filename.lower().endswith('.pdf'):
                    try:
                        # Decode filename if needed
                        decoded_parts = decode_header(filename)
                        decoded_filename = ""
                        for part_data, encoding in decoded_parts:
                            if isinstance(part_data, bytes):
                                decoded_filename += part_data.decode(encoding or 'utf-8', errors='ignore')
                            else:
                                decoded_filename += part_data
                        
                        # Create unique filename with request number
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        safe_filename = f"{request_number}_approved_{timestamp}.pdf"
                        file_path = PDF_STORAGE_PATH / safe_filename
                        
                        # Save file
                        pdf_data = part.get_payload(decode=True)
                        with open(file_path, 'wb') as f:
                            f.write(pdf_data)
                        
                        saved_files.append(str(file_path))
                        print(f"   ✅ Saved PDF: {safe_filename} ({len(pdf_data)} bytes)")
                        
                    except Exception as e:
                        print(f"   ❌ Failed to save PDF attachment: {e}")
                else:
                    print(f"   ⚠️  Attachment is not a PDF: {filename}")
        
        if attachment_count == 0:
            print(f"   ℹ️  No attachments found in email")
    else:
        print(f"   ℹ️  Email is not multipart")
    
    return saved_files


def check_email_replies():
    """
    Check email inbox for approval/rejection replies
    """
    print(f"\n{'='*60}")
    print(f"🔍 Checking email replies at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Connect to IMAP server
        print(f"📧 Connecting to {IMAP_SERVER}:{IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("✅ Connected successfully\n")
        
        # Select inbox
        mail.select('INBOX')
        
        # Search for unread emails with special price request subject
        # ค้นหาเฉพาะ email ที่มี "Special Price Request" ใน subject
        status, messages = mail.search(None, 'UNSEEN SUBJECT "Special Price Request"')
        
        if status != 'OK':
            print("❌ Failed to search emails")
            return
        
        email_ids = messages[0].split()
        
        if not email_ids:
            print("📭 No unread emails found")
            mail.close()
            mail.logout()
            return
        
        print(f"📬 Found {len(email_ids)} unread email(s)\n")
        
        processed_count = 0
        
        for email_id in email_ids:
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Get subject
                subject = decode_email_subject(msg.get('Subject', ''))
                from_email = msg.get('From', '')
                
                print(f"📨 Processing email:")
                print(f"   From: {from_email}")
                print(f"   Subject: {subject}")
                
                # Extract request number
                request_number = extract_request_number(subject)
                
                if not request_number:
                    print(f"   ⚠️  Not a special price request email\n")
                    continue
                
                print(f"   Request Number: {request_number}")
                
                # Get email body
                body = get_email_body(msg)
                
                # Extract PDF attachments
                pdf_files = extract_pdf_attachments(msg, request_number)
                
                # Check for approval decision
                decision = check_approval_decision(body)
                
                if not decision:
                    print(f"   ⚠️  No APPROVE/REJECT found in email body\n")
                    continue
                
                decision_type, reason = decision
                print(f"   Decision: {decision_type.upper()}")
                
                # Get request detail
                request_data = get_request_detail(request_number)
                
                if not request_data:
                    print(f"   ❌ Request {request_number} not found\n")
                    continue
                
                # Check if already processed
                if request_data['status'] != 'pending':
                    print(f"   ⚠️  Request already {request_data['status']}\n")
                    continue
                
                # Process approval/rejection
                if decision_type == 'approve':
                    success = approve_request(request_number, from_email, pdf_files)
                    if success:
                        print(f"   ✅ APPROVED by {from_email}")
                        if pdf_files:
                            print(f"   📎 {len(pdf_files)} PDF file(s) attached")
                        processed_count += 1
                    else:
                        print(f"   ❌ Failed to approve")
                
                elif decision_type == 'reject':
                    success = reject_request(request_number, reason or "ไม่ระบุเหตุผล")
                    if success:
                        print(f"   ❌ REJECTED: {reason}")
                        processed_count += 1
                    else:
                        print(f"   ❌ Failed to reject")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error processing email: {e}\n")
                continue
        
        # Close connection
        mail.close()
        mail.logout()
        
        print(f"\n{'='*60}")
        print(f"✅ Processed {processed_count} email(s)")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error connecting to email server: {e}")


if __name__ == "__main__":
    check_email_replies()
