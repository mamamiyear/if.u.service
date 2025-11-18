import logging
import smtplib
from email.mime.text import MIMEText
from typing import Protocol
from .config import get_instance as get_config

class Mailer(Protocol):
    def send(self, to_email: str, subject: str, content: str) -> bool:
        ...


class FakeMailer:
    def __init__(self) -> None:
        conf = get_config()
        self.fake_message = conf.get('fake_mailer', 'message', fallback="FakeEmail")
    def send(self, to_email: str, subject: str, content: str) -> bool:
        logging.info(f"{self.fake_message}: to_email={to_email}, subject={subject}, content={content}")
        return True


class RealMailer:
    def __init__(self):
        conf = get_config()
        self.smtp_host = conf.get('real_mailer', 'smtp_host', fallback=None)
        self.smtp_port = conf.getint('real_mailer', 'smtp_port', fallback=587)
        self.smtp_user = conf.get('real_mailer', 'smtp_user', fallback=None)
        self.smtp_pass = conf.get('real_mailer', 'smtp_pass', fallback=None)
        self.from_email = conf.get('real_mailer', 'from_email', fallback=self.smtp_user)

    def send(self, to_email: str, subject: str, content: str) -> bool:
        if not self.smtp_host or not self.smtp_user or not self.smtp_pass:
            return False
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.from_email, [to_email], msg.as_string())
            server.quit()
            return True
        except Exception:
            return False


_mailer: Mailer = None


def init(type: str = 'real'):
    global _mailer
    if type == 'real':
        _mailer = RealMailer()
    else:
        _mailer = FakeMailer()


def get_instance() -> Mailer:
    return _mailer