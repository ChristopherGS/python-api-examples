import typing as t

import acme.messages
import josepy
from botocore.client import Config
from fastapi import Depends, HTTPException, Header, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from pydantic import ValidationError

from app.db.session import SessionWithUserID as Session
from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    # It is implied that all scopes are for objects within your visibility level.
    # Unless you are a superuser and then your visibility level is all objects.
    scopes={
        "token:refresh": "Allow the creation of new tokens",
        "me": "Read/Modify information about the current user.",
    },
    auto_error=False,  # Do not automatically error if authorisation headers is missing
)


def get_db() -> t.Generator:
    db = SessionLocal()
    db.current_user_id = None
    try:
        yield db
    finally:
        db.close()


def get_current_user(allow_public: bool = False):  # type: ignore
    async def get_current_user(
        security_scopes: SecurityScopes,
        token: str = Depends(reusable_oauth2),
        db: Session = Depends(get_db),
    ) -> t.Optional[models.User]:
        if security_scopes.scopes:
            authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        else:
            authenticate_value = "Bearer"
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )
        if token is None:
            if allow_public:
                return None
            raise credentials_exception
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[security.ALGORITHM],
                audience=settings.DOMAIN,
            )
            username: str = payload.get("sub")
            if username is None:
                if allow_public:
                    return None
                raise credentials_exception
            token_data: t.Union[schemas.AccessTokenPayload, schemas.RefreshTokenPayload]
            if payload["type"] == "refresh_token":
                token_data = schemas.RefreshTokenPayload(**payload)
            else:
                token_data = schemas.AccessTokenPayload(**payload)

        except (jwt.JWTError, ValidationError):
            if allow_public:
                return None
            raise credentials_exception
        user: t.Optional[models.User]
        if (
            isinstance(token_data, schemas.AccessTokenPayload)
            and str(token_data.sub) == settings.build.TEMP_STUDENT_USER_ID
        ):
            school = crud.school.get(
                db, id=token_data.schools[0], check_permissions=False
            )
            if not school:
                raise credentials_exception
            user = crud.user.get_fake_student_user(db, school)
        else:
            user = crud.user.get(db, id=token_data.sub, check_permissions=False)
        if not user:
            if allow_public:
                return None
            raise credentials_exception

        if crud.user.is_superuser(user):
            # Skip scope validation if user is superuser
            return user

        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                if allow_public:
                    return None
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions. In some cases you may need to "
                    "logout and login again.",
                    headers={"WWW-Authenticate": authenticate_value},
                )
        db.current_user_id = user.id  # type: ignore
        return user

    return get_current_user


async def get_user_from_refresh_token(
    security_scopes: SecurityScopes,
    current_user: models.User = Security(get_current_user(), scopes=["token:refresh"]),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_user(allow_public: bool = False) -> t.Any:
    def get_current_active_user(
        current_user: models.User = Security(
            get_current_user(allow_public=allow_public), scopes=["me"]
        )
    ) -> models.User:
        if allow_public and current_user is None:
            return None
        if not crud.user.is_active(current_user):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    return get_current_active_user
