from typing import Optional, MutableMapping, List, Union
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm.session import Session
from jose import jwt

from app.models import User
from app.config import settings

JWTPayloadMapping = MutableMapping[
    str, Union[datetime, bool, str, List[str], List[int]]
]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate(
        *,
        email: str,
        password: str,
        db: Session,
) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_jwt_payload(
        user: User,
) -> JWTPayloadMapping:
    payload: JWTPayloadMapping = {}
    payload["aud"] = [settings.DOMAIN]
    return payload


def create_access_token(
        sub: str,
        payload: JWTPayloadMapping,
) -> str:
    return _create_token(
        token_type="access_token",
        lifetime=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        sub=sub,
        payload=payload,
    )


def _create_token(
        token_type: str,
        lifetime: timedelta,
        sub: str,
        payload: Optional[JWTPayloadMapping] = None,
) -> str:
    payload = payload if payload else {}
    expire = datetime.utcnow() + lifetime
    payload["type"] = token_type
    payload["exp"] = expire
    payload["iat"] = datetime.utcnow()
    payload["sub"] = str(sub)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)