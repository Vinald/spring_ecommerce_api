import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
import os
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from src.Logger import Logger
from src.Config import Config

# Log in ivr/ and not src/
working_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logger = Logger(working_dir)

config = Config(working_dir, logger)
config.set_section('email')

username = config.get('username')
password = config.get('password')
mail_port = config.get('port')
mail_host = config.get('host')
email_from = username


class Email:
    def __init__(self, to_recipients: list, subject: str, body_message: str, cc_recipients: list = None,
                 attachment_paths: list = None):
        self.to_recipients = to_recipients
        self.cc_recipients = cc_recipients
        self.subject = subject
        self.body_message = body_message
        self.attachment_paths = attachment_paths
        if self.to_recipients is not None and not isinstance(self.to_recipients, list):
            logger.log_info("[EMAIL]: 'To' Recipients not provided in list format")
            exit(1)
        if self.cc_recipients is not None and not isinstance(self.cc_recipients, list):
            logger.log_info("[EMAIL]: 'Cc' Recipients not provided in list format")
            exit(1)
        if self.attachment_paths is not None and not isinstance(self.attachment_paths, list):
            logger.log_info("[EMAIL]: Attached file paths not provided in list format")
            exit(1)

    def send_email(self):
        if self.cc_recipients is not None:
            recipients = self.to_recipients + self.cc_recipients
        else:
            recipients = self.to_recipients

        msg = MIMEMultipart()
        msg["From"] = email_from
        msg["To"] = ','.join(self.to_recipients)
        if self.cc_recipients is not None:
            msg["Cc"] = ','.join(self.cc_recipients)
        msg["Subject"] = self.subject
        msg.preamble = self.body_message
        body = MIMEText(msg.preamble, "plain")
        msg.attach(body)

        if self.attachment_paths is not None:
            for each_path in self.attachment_paths:
                file_name = os.path.basename(each_path)
                ctype, encoding = mimetypes.guess_type(each_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)

                if maintype == "text":
                    fp = open(each_path)
                    # Note: we should handle calculating the charset
                    attachment = MIMEText(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == "image":
                    fp = open(each_path, "rb")
                    attachment = MIMEImage(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == "audio":
                    fp = open(each_path, "rb")
                    attachment = MIMEAudio(fp.read(), _subtype=subtype)
                    fp.close()
                else:
                    fp = open(each_path, "rb")
                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(fp.read())
                    fp.close()
                    encoders.encode_base64(attachment)
                attachment.add_header("Content-Disposition", "attachment", filename=file_name)
                msg.attach(attachment)
        server = smtplib.SMTP(mail_host, mail_port)
        try:
            server.starttls()
            server.login(username, password)
            server.sendmail(email_from, recipients, msg.as_string())
            logger.log_info('[EMAIL]: Email to {}, Subject: {} sent successfully'.format(recipients, self.subject))
            print('Email Sent Successfully...')
        except Exception as e:
            print('Email Send Failed...')
            logger.log_info("[EMAIL]: Failed to send email with error: {}".format(e))
        finally:
            server.quit()
