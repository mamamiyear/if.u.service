import logging
from typing import Protocol
import requests
from .config import get_instance as get_config


class SMS(Protocol):
    def send(self, phone: str, content: str) -> bool:
        ...


class FakeSMS:
    def __init__(self) -> None:
        conf = get_config()
        self.fake_message = conf.get('fake_sms', 'message', fallback="FakeSMS")
    def send(self, phone: str, content: str) -> bool:
        logging.info(f"{self.fake_message}: phone={phone}, content={content}")
        return True


class RealSMS:
    def __init__(self):
        conf = get_config()
        self.webhook_url = conf.get('real_sms', 'webhook_url', fallback=None)
        self.webhook_token = conf.get('real_sms', 'webhook_token', fallback=None)

    def send(self, phone: str, content: str) -> bool:
        if not self.webhook_url:
            return False
        try:
            headers = {'Authorization': f'Bearer {self.webhook_token}'} if self.webhook_token else {}
            data = {'phone': phone, 'content': content}
            resp = requests.post(self.webhook_url, json=data, headers=headers, timeout=5)
            return resp.status_code >= 200 and resp.status_code < 300
        except Exception:
            return False


_sms: SMS = None


def init(type: str = 'real'):
    global _sms
    if type == 'real':
        _sms = RealSMS()
    else:
        _sms = FakeSMS()


def get_instance() -> SMS:
    return _sms