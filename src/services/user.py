import uuid
import hmac
import base64
import os
from datetime import datetime, timedelta
from typing import Optional
from utils.error import ErrorCode, error
from utils import rldb, mailer, sms, config
from models.user import (
    User,
    UserRLDBModel,
    VerificationCode,
    VerificationCodeRLDBModel,
    UserToken,
    UserTokenRLDBModel,
)


class UserService:
    def __init__(self):
        self.rldb = rldb.get_instance()
        self.mailer = mailer.get_instance()
        self.sms = sms.get_instance()
        self.conf = config.get_instance()

    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        salt = salt if salt else base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
        digest = hmac.new(salt.encode('utf-8'), password.encode('utf-8'), 'sha256').digest()
        return f"{salt}:{base64.urlsafe_b64encode(digest).decode('utf-8')}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        parts = password_hash.split(':')
        if len(parts) != 2:
            return False
        salt = parts[0]
        return self._hash_password(password, salt) == password_hash

    def send_code(self, target_type: str, target: str, scene: str) -> error:
        scens = {
            "register": "注册",
            "update": "信息更新",
            # "login": "登录",
        }
        if scene not in scens:
            return error(ErrorCode.MODEL_ERROR, f'scene {scene} not supported')
        scene_name = scens.get(scene, scene)
        code = f"{uuid.uuid4().int % 1000000:06d}"
        expires = datetime.now() + timedelta(minutes=10)
        vc = VerificationCode(
            id=uuid.uuid4().hex,
            target_type=target_type,
            target=target,
            code=code,
            scene=scene,
            expires_at=expires,
        )
        self.rldb.upsert(vc.to_rldb_model())
        content = f"IF.U服务{scene_name}验证码: {code}, 10分钟内有效"
        sent = True
        if target_type == 'email':
            sent = self.mailer.send(target, f'IF.U服务{scene_name}验证码', content) if self.mailer else False
        elif target_type == 'phone':
            sent = self.sms.send(target, content) if self.sms else False
        if not sent:
            return error(ErrorCode.RLDB_ERROR, 'send code failed')
        return error(ErrorCode.SUCCESS, '')

    def _get_user_by_identifier(self, email: Optional[str], phone: Optional[str]) -> Optional[User]:
        if email:
            users = self.rldb.query(UserRLDBModel, email=email, limit=1)
            if users:
                return User.from_rldb_model(users[0])
        if phone:
            users = self.rldb.query(UserRLDBModel, phone=phone, limit=1)
            if users:
                return User.from_rldb_model(users[0])
        return None

    def register(self, user: User, code: str) -> (str, error):
        if not user.email and not user.phone:
            return '', error(ErrorCode.MODEL_ERROR, 'email or phone required')
        existed = self._get_user_by_identifier(user.email, user.phone)
        if existed:
            return '', error(ErrorCode.MODEL_ERROR, 'user existed')
        target_type = 'phone' if user.phone else 'email'
        target = user.phone if user.phone else user.email
        vc_list = self.rldb.query(
            VerificationCodeRLDBModel,
            target_type=target_type,
            target=target,
            scene='register',
            limit=1,
        )
        if not vc_list:
            return '', error(ErrorCode.MODEL_ERROR, 'code not found')
        vc = vc_list[0]
        if vc.code != code or vc.expires_at < datetime.now() or vc.used_at is not None:
            return '', error(ErrorCode.MODEL_ERROR, 'invalid code')
        vc.used_at = datetime.now()
        self.rldb.upsert(vc)
        user.id = uuid.uuid4().hex
        hashed = self._hash_password(user.password_hash)
        user.password_hash = hashed
        self.rldb.upsert(user.to_rldb_model())
        return user.id, error(ErrorCode.SUCCESS, '')

    def login(self, email: Optional[str], phone: Optional[str], password: str) -> (dict, error):
        u = self._get_user_by_identifier(email, phone)
        if not u:
            return {}, error(ErrorCode.MODEL_ERROR, 'user not found')
        if not self._verify_password(password, u.password_hash):
            return {}, error(ErrorCode.MODEL_ERROR, 'invalid password')
        ttl_days = self.conf.getint('auth', 'token_ttl_days', fallback=30)
        expired_at = datetime.now() + timedelta(days=ttl_days)
        token_raw = f"{u.id}.{uuid.uuid4().hex}.{int(expired_at.timestamp())}"
        secret = self.conf.get('auth', 'jwt_secret', fallback='dev-secret')
        signature = hmac.new(secret.encode('utf-8'), token_raw.encode('utf-8'), 'sha256').digest()
        token = base64.urlsafe_b64encode(token_raw.encode('utf-8')).decode('utf-8') + '.' + base64.urlsafe_b64encode(signature).decode('utf-8')
        ut = UserToken(id=uuid.uuid4().hex, user_id=u.id, token=token, expired_at=expired_at, revoked=False)
        self.rldb.upsert(ut.to_rldb_model())
        return {'token': token, 'expired_at': int(expired_at.timestamp())}, error(ErrorCode.SUCCESS, '')

    def logout(self, token: str) -> error:
        tokens = self.rldb.query(UserTokenRLDBModel, token=token, limit=1)
        if not tokens:
            return error(ErrorCode.MODEL_ERROR, 'token not found')
        t = tokens[0]
        t.revoked = True
        self.rldb.upsert(t)
        return error(ErrorCode.SUCCESS, '')

    def delete_user(self, user_id: str) -> error:
        u = self.rldb.get(UserRLDBModel, user_id)
        if not u:
            return error(ErrorCode.MODEL_ERROR, 'user not found')
        self.rldb.delete(u)
        return error(ErrorCode.SUCCESS, '')

    def get(self, user_id: str) -> (User, error):
        u = self.rldb.get(UserRLDBModel, user_id)
        if not u:
            return None, error(ErrorCode.MODEL_ERROR, 'user not found')
        return User.from_rldb_model(u), error(ErrorCode.SUCCESS, '')

    def update_profile(self, user_id: str, nickname: str = None, avatar_link: str = None, phone: str = None, email: str = None) -> (User, error):
        u = self.rldb.get(UserRLDBModel, user_id)
        if not u:
            return None, error(ErrorCode.MODEL_ERROR, 'user not found')
        has_email = bool(u.email)
        has_phone = bool(u.phone)
        if nickname is not None:
            u.nickname = nickname
        if avatar_link is not None:
            u.avatar_link = avatar_link
        if email is not None:
            new_email = email
            if has_email:
                if not has_phone:
                    return None, error(ErrorCode.MODEL_ERROR, 'email update requires phone exists')
            conflicts = self.rldb.query(UserRLDBModel, email=new_email, limit=1)
            if conflicts and conflicts[0].id != user_id:
                return None, error(ErrorCode.MODEL_ERROR, 'email existed')
            u.email = new_email
        if phone is not None:
            new_phone = phone
            if has_phone:
                if not has_email:
                    return None, error(ErrorCode.MODEL_ERROR, 'phone update requires email exists')
            conflicts = self.rldb.query(UserRLDBModel, phone=new_phone, limit=1)
            if conflicts and conflicts[0].id != user_id:
                return None, error(ErrorCode.MODEL_ERROR, 'phone existed')
            u.phone = new_phone
        self.rldb.upsert(u)
        return User.from_rldb_model(u), error(ErrorCode.SUCCESS, '')

    def update_phone_with_code(self, user_id: str, new_phone: str, code: str) -> (User, error):
        vc_list = self.rldb.query(
            VerificationCodeRLDBModel,
            target_type='phone',
            target=new_phone,
            scene='update',
            limit=1,
        )
        if not vc_list:
            return None, error(ErrorCode.MODEL_ERROR, 'code not found')
        vc = vc_list[0]
        if vc.code != code or vc.expires_at < datetime.now() or vc.used_at is not None:
            return None, error(ErrorCode.MODEL_ERROR, 'invalid code')
        vc.used_at = datetime.now()
        self.rldb.upsert(vc)
        return self.update_profile(user_id, phone=new_phone)

    def update_email_with_code(self, user_id: str, new_email: str, code: str) -> (User, error):
        vc_list = self.rldb.query(
            VerificationCodeRLDBModel,
            target_type='email',
            target=new_email,
            scene='update',
            limit=1,
        )
        if not vc_list:
            return None, error(ErrorCode.MODEL_ERROR, 'code not found')
        vc = vc_list[0]
        if vc.code != code or vc.expires_at < datetime.now() or vc.used_at is not None:
            return None, error(ErrorCode.MODEL_ERROR, 'invalid code')
        vc.used_at = datetime.now()
        self.rldb.upsert(vc)
        return self.update_profile(user_id, email=new_email)


user_service = None


def init():
    global user_service
    user_service = UserService()


def get_instance() -> UserService:
    return user_service