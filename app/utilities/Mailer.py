import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.utilities.Config import Config
from app.utilities.Logger import Logger


class Mailer:
    def __init__(self, config: Config, logger: Logger):
        self.__to = None
        self.__cc = None
        self.__subject = None
        self.__message_body = None

        self.__logger = logger

        self.__user = config.get('user')
        self.__pass = config.get('pass')
        self.__port = config.get_int('port')
        self.__host = config.get('host')

    def set_to(self, to_recipients):
        self.__to = to_recipients

    def set_cc(self, cc_recipients):
        self.__cc = cc_recipients

    def set_subject(self, subject):
        self.__subject = subject

    def set_message(self, message):
        self.__message_body = message

    def send_email(self):
        if self.__cc is not None:
            recipients = self.__to + self.__cc
        else:
            recipients = self.__to

        msg = MIMEMultipart()
        msg["From"] = self.__user
        msg["To"] = ','.join(self.__to)
        if self.__cc is not None:
            msg["Cc"] = ','.join(self.__cc)
        msg["Subject"] = self.__subject
        msg.preamble = self.__message_body
        body = MIMEText(msg.preamble, "plain")
        msg.attach(body)

        server = smtplib.SMTP(self.__host, self.__port)
        try:
            server.starttls()
            server.login(self.__user, self.__pass)
            server.sendmail(self.__user, recipients, msg.as_string())
            self.__logger.log_info(f'[EMAIL]: Email to {recipients}, Subject: {self.__subject} sent successfully')
        except Exception as e:
            self.__logger.log_info(f'[EMAIL]: Failed to send email with error: {str(e)}')
        finally:
            server.quit()
