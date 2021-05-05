from fastapi import APIRouter

from app import schemas
from app import __version__
from app.auth import authenticate
from app.api.deps import get_current_user

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.post("/token")
async def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user_dict = authenticate(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/signup", response_model=schemas.User, status_code=201)
def create_user_signup(
        *,
        db: Session = Depends(deps.get_db),
        user_in: schemas.UserCreateRestricted,
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    create_user = schemas.UserCreate(**user_in.dict())

    user = crud.user.get_by_email(
        db, email=create_user.email, client_id=create_user.client_id
    )
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    user = crud.user.create(db, obj_in=create_user)
    db.commit()

    return user