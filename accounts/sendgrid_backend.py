"""
SendGrid Email Backend for Django (HTTP API - Railway Compatible)

This backend uses SendGrid's HTTP API instead of SMTP because Railway blocks SMTP ports.
Compatible with Django's email system - drop-in replacement for SMTP backend.
"""
import logging
import base64
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition, ContentId

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """
    SendGrid HTTP API Email Backend
    
    Railway blocks SMTP ports (587, 465, 25) so we use SendGrid's HTTP API instead.
    This works perfectly on Railway since HTTP/HTTPS are allowed.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        
        if not self.api_key:
            logger.error("SENDGRID_API_KEY not found in settings!")
            if not fail_silently:
                raise ValueError("SENDGRID_API_KEY must be set in settings")
        
        self.client = SendGridAPIClient(self.api_key)
        logger.info("SendGrid HTTP API backend initialized")
    
    def send_messages(self, email_messages):
        """
        Send multiple email messages via SendGrid HTTP API
        
        Args:
            email_messages: List of EmailMessage objects
        
        Returns:
            int: Number of successfully sent messages
        """
        if not email_messages:
            return 0
        
        success_count = 0
        
        for message in email_messages:
            try:
                sent = self._send(message)
                if sent:
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to send email via SendGrid: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return success_count
    
    def _send(self, message):
        """
        Send a single email message via SendGrid HTTP API
        
        Args:
            message: Django EmailMessage object
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Extract sender
            from_email = message.from_email
            if not from_email:
                from_email = settings.DEFAULT_FROM_EMAIL
            
            # Get recipients
            to_emails = message.to
            if not to_emails:
                logger.warning("No recipients specified")
                return False
            
            # Get subject
            subject = message.subject
            
            # Get body content (prefer HTML)
            if hasattr(message, 'alternatives') and message.alternatives:
                # HTML email
                html_content = message.alternatives[0][0]
                plain_content = message.body
            else:
                # Plain text only
                plain_content = message.body
                html_content = None
            
            # Send to each recipient (SendGrid requires one-by-one for multiple recipients)
            for to_email in to_emails:
                try:
                    # Create SendGrid Mail object
                    mail = Mail(
                        from_email=Email(from_email),
                        to_emails=To(to_email),
                        subject=subject,
                        plain_text_content=Content("text/plain", plain_content)
                    )
                    
                    # Add HTML content if available
                    if html_content:
                        mail.add_content(Content("text/html", html_content))

                    
                    # Handle inline attachments (for cid: references)
                    if hasattr(message, 'attachments') and message.attachments:
                        for attachment in message.attachments:
                            try:
                                # Check if it's a MIMEImage or tuple
                                if hasattr(attachment, 'get_content_type'):
                                    # MIMEBase object (like MIMEImage)
                                    content_type = attachment.get_content_type()
                                    content_id = attachment.get('Content-ID', '').strip('<>')
                                    filename = attachment.get_filename() or 'attachment'
                                    file_data = attachment.get_payload(decode=True)
                                    
                                    # Convert to base64 for SendGrid
                                    encoded_file = base64.b64encode(file_data).decode()
                                    
                                    # Create proper inline attachment for SendGrid
                                    # Key insight: Use raw dict structure for SendGrid API v3
                                    attachment_data = {
                                        'content': encoded_file,
                                        'type': content_type,
                                        'filename': content_id,  # Use CID as filename
                                        'disposition': 'inline',  # String, not Disposition object
                                        'content_id': content_id
                                    }
                                    
                                    sg_attachment = Attachment()
                                    sg_attachment.file_content = FileContent(encoded_file)
                                    sg_attachment.file_name = FileName(content_id)
                                    sg_attachment.file_type = FileType(content_type) 
                                    sg_attachment.disposition = Disposition('inline')
                                    sg_attachment.content_id = ContentId(content_id)
                                    
                                    mail.add_attachment(sg_attachment)
                                    
                                    logger.info(f"Inline attachment: CID={content_id}")
                                    
                            except Exception as e:
                                logger.warning(f"Failed to process attachment: {str(e)}")
                    
                    # Send via HTTP API
                    logger.info(f"Sending email via SendGrid HTTP API to: {to_email}")
                    
                    response = self.client.send(mail)
                    
                    if response.status_code in [200, 201, 202]:
                        logger.info(f"Email sent successfully to {to_email} | Status: {response.status_code}")
                    else:
                        logger.error(f"SendGrid returned status {response.status_code}")
                        return False
                
                except Exception as e:
                    logger.error(f"Failed to send to {to_email}: {str(e)}")
                    
                    if not self.fail_silently:
                        raise
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error in _send: {str(e)}")
            if not self.fail_silently:
                raise
            return False
