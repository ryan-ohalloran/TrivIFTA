import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import logging
from daily_compliance_job.models import EmailRecipient, EmailSender
from datetime import date

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, subject: str, body: str, date: date = None, attachment: bytes = None, attachment_name: str = '') -> None:
        self.subject = subject
        self.body = body
        self.attachment = attachment
        self.attachment_name = attachment_name
        self.date = date

    def send(self) -> bool:
        '''
        Send the email
        returns True if the email was sent successfully, False otherwise
        '''
        # get the email sender 
        sender = EmailSender.objects.first()
        if not sender:
            logger.error("No email sender configured")
            return False

        # get the email recipients
        recipients = [recipient.email for recipient in EmailRecipient.objects.all()]

        try:
            # Set up the SMTP server
            server = smtplib.SMTP(sender.smtp_server, sender.smtp_port)
            # Using tls
            server.starttls()
            try:
                server.login(sender.email, sender.get_smtp_password())
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Error authenticating with SMTP server: {e}")
                return False

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = sender.email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = self.subject

            # if the date was provided and that date is a weekend, add a note to the email
            if self.date and self.date.weekday() >= 5:
                day_of_week = 'Saturday' if self.date.weekday() == 5 else 'Sunday'
                self.body += f"\n\nNote: {self.date.month}/{self.date.day}/{self.date.year} is a {day_of_week}. There may be less data than usual.\n"
                
            msg.attach(MIMEText(self.body, 'plain'))

            # Add the attachment if provided
            if self.attachment:
                attachment = MIMEApplication(self.attachment, name=self.attachment_name)
                attachment['Content-Disposition'] = f'attachment; filename="{self.attachment_name}"'
                msg.attach(attachment)

            # Send the email
            server.send_message(msg)

            server.quit()
            logger.info("Emails sent successfully.")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
        
        return True