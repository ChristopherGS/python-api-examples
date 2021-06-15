from app import schemas
from app import __version__
from app.auth import authenticate, get_password_hash, get_user_jwt_payload, create_access_token
from app.api import deps
from app.models import User

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.session import Session

from typing import Optional, Any

api_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



@api_router.get("/", response_model=schemas.Msg, status_code=200)
def root() -> dict:
    """
    Root Get
    """
    return {"msg": "This is the Example API"}


@api_router.get("/health", response_model=schemas.Health, status_code=200)
def health() -> dict:
    """
    Root Get
    """
    return {"name": "Example API", "version": __version__}


async def get_current_user(token: str = Depends(deps.oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@api_router.post("/token")
async def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = authenticate(
        email=form_data.username,
        password=form_data.password,
        db=db
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user_jwt_payload = get_user_jwt_payload(user)
    return {
        "access_token": create_access_token(user.id, user_jwt_payload),
        "token_type": "bearer",
    }


@api_router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@api_router.post("/signup", response_model=schemas.User, status_code=201)
def create_user_signup(
        *,
        db: Session = Depends(deps.get_db),
        user_in: schemas.CreateUser,
) -> Any:
    """
    Create new user without the need to be logged in.
    """

    user = db.query(User
                    ).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    create_user_data = user_in.dict()
    create_user_data.pop("password")
    db_obj = User(**create_user_data)
    db_obj.hashed_password = get_password_hash(user_in.password)
    db.add(db_obj)
    db.commit()

    return schemas.User(**create_user_data)
