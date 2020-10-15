import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
import os
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from app.core import config, logger


config.set_section('email-server')

username = config.get('user')
password = config.get('pass')
mail_port = config.get_int('port')
mail_host = config.get('host')
email_from = username


class Email:
    def __init__(
        self,
        to_recipients: list,
        subject: str,
        body_message: str,
        cc_recipients: list = None,
        attachment_paths: list = None
    ):
        self.__to = to_recipients
        self.__cc = cc_recipients
        self.__subject = subject
        self.__message_body = body_message
        self.__attachment_paths = attachment_paths

        if self.__to is not None and not isinstance(self.__to, list):
            logger.log_info("[EMAIL]: 'To' Recipients not provided in list format")
        if self.__cc is not None and not isinstance(self.__cc, list):
            logger.log_info("[EMAIL]: 'Cc' Recipients not provided in list format")
        if self.__attachment_paths is not None and not isinstance(self.__attachment_paths, list):
            logger.log_info("[EMAIL]: Attached file paths not provided in list format")

    def send_email(self):
        if self.__cc is not None:
            recipients = self.__to + self.__cc
        else:
            recipients = self.__to

        msg = MIMEMultipart()
        msg["From"] = email_from
        msg["To"] = ','.join(self.__to)
        if self.__cc is not None:
            msg["Cc"] = ','.join(self.__cc)
        msg["Subject"] = self.__subject
        msg.preamble = self.__message_body
        body = MIMEText(msg.preamble, "plain")
        msg.attach(body)

        if self.__attachment_paths is not None:
            for each_path in self.__attachment_paths:
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
            logger.log_info('[EMAIL]: Email to {}, Subject: {} sent successfully'.format(recipients, self.__subject))
        except Exception as e:
            logger.log_info("[EMAIL]: Failed to send email with error: {}".format(e))
        finally:
            server.quit()
