import asyncio
from sqlalchemy import  select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from passlib.context import CryptContext
import jwt, json
from datetime import datetime, timedelta
from models import User
from schemas import CreateCvRequest,CreateUserRequest,UserLoginRequest,UpdateCvRequest,UpdateUserRequest,CvResponse,UserResponse
import json
import uvicorn
import random
from models import Cv,User

from fastapi.middleware.cors import CORSMiddleware
from models import Base

from dotenv import load_dotenv

import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_BASE = os.environ.get('DB_BASE')

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_BASE}"
#DATABASE_URL = f"mysql+aiomysql://root@localhost:3306/cv_magique"
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False) # type: ignore

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    print(DATABASE_URL)
    await asyncio.create_task(create_tables())


# Credentials Elements of JWTauthentication
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"])
SECRET_KEY = os.environ.get("SECRET_KEY")  # Change this to your desired secret key
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")


# Define the get_session function as a dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

### the API CRUD ###
#API root
@app.get("/")
async def welcome_api():
    return "this is a backend api of cvmagique"



pwd_context = CryptContext(schemes=["bcrypt"])

# Function to hash the password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify the password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Function to generate the access token
def create_access_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Function to decode the access token
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/register", status_code=201)
async def register_user(request: CreateUserRequest, session: AsyncSession = Depends(get_session)):
    # Check if the email is already registered
    existing_user = await session.execute(select(User).where(User.email == request.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create a new user
    user = User(
        fullname=request.fullname,
        email=request.email,
        avatar=request.avatar,
        hashed_password=hash_password(request.hashed_password),
        is_admin=False,
    )
    session.add(user)
    await session.commit()

    # Return the registered user
    message = f"User with ID :{user.id} created successfully"
    return {"user":user, "message":message}

@app.post("/login")
async def login_user(request: UserLoginRequest, session: AsyncSession = Depends(get_session)):
    # Check if the user exists
    user = await session.execute(select(User).where(User.email == request.email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify the password
    if not verify_password(request.hashed_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate the access token
    access_token = create_access_token(user.id)

    # Return the access token
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
async def get_current_user(session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the current user from the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a dictionary from the user object
    user_dict = {
        "fullname": user.fullname,
        "email": user.email,
        "avatar": user.avatar
    }

    # Return the user data
    return user_dict


@app.get("/me/cvs")
async def get_current_user_cvs(session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CVs of the current user from the database
    cvs = await session.execute(select(Cv).where(Cv.user_id == user_id))
    cvs = cvs.scalars().all()

    # Convert the CV objects to dictionaries
    cvs_dicts = []
    for cv in cvs:
        try:
            experiences = json.loads(cv.experiences)
        except json.JSONDecodeError:
            experiences = cv.experiences  # Store as string

        try:
            education = json.loads(cv.education)
        except json.JSONDecodeError:
            education = cv.education  # Store as string

        try:
            languages = json.loads(cv.languages)
        except json.JSONDecodeError:
            languages = cv.languages  # Store as string

        try:
            loisirs = json.loads(cv.loisirs)
        except json.JSONDecodeError:
            loisirs = cv.loisirs  # Store as string

        cv_dict = {
            "id": cv.id,
            "nom": cv.nom,
            "prenom": cv.prenom,
            "address": cv.address,
            "email": cv.email,
            "city": cv.city,
            "country": cv.country,
            "postalcode": cv.postalcode,
            "tele": cv.tele,
            "brief": cv.brief,
            "img_url": cv.img_url,
            "style": cv.style,
            "color": cv.color,
            "experiences": experiences,
            "education": education,
            "languages": languages,
            "loisirs": loisirs,
            "user_id": cv.user_id
        }

        cvs_dicts.append(cv_dict)

    # Return the CV data
    return cvs_dicts


#generate random id
def generate_random_id(length=10):
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

#create user cv
@app.post("/me/cvs")
async def create_cv(request: CreateCvRequest, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    cv_id = generate_random_id()
    # Create a new CV object from the request data
    cv = Cv(
        id = cv_id,
        nom=request.nom,
        prenom=request.prenom,
        address=request.address,
        email=request.email,
        city=request.city,
        country=request.country,
        postalcode=request.postalcode,
        tele=request.tele,
        brief=request.brief,
        img_url=request.img_url,
        style=request.style,
        color=request.color,
        experiences=json.dumps(request.experiences),
        education=json.dumps(request.education),
        languages=json.dumps(request.languages),
        loisirs=json.dumps(request.loisirs),
        user_id=user_id
    )

    # Save the new CV to the database
    session.add(cv)
    await session.commit()

    # Create a success message
    message = f"CV with ID {cv.id} created successfully"

    # Return the created CV and the success message as a response
    return {
        "cv": cv,
        "message": message
    }


#update cv 
@app.put("/me/cvs/{cv_id}")
async def update_cv(
    cv_id: str,
    cv_data: UpdateCvRequest,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV from the database
    cv = await session.get(Cv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Check if the CV belongs to the current user
    if cv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Update the CV with the provided data
    for field, value in cv_data.dict().items():
        setattr(cv, field, value)

    # Commit the changes to the database
    await session.commit()
    
    # Convert the cv object to a dictionary
    cv_dict = cv.__dict__

    # Remove the "_sa_instance_state" attribute
    cv_dict.pop("_sa_instance_state", None)

    # Return the updated CV as a dictionary
    return {"CV":cv_dict,"message":"CV Updated successfully"}


@app.delete("/me/cvs/{cv_id}")
async def delete_cv(
    cv_id: str,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV from the database
    cv = await session.get(Cv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Check if the CV belongs to the current user
    if cv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Delete the CV from the database
    await session.delete(cv)
    await session.commit()

    # Return a success message
    return {"message": "CV deleted successfully"}





@app.get("/users")
async def get_all_users(session: AsyncSession = Depends(get_session)):
    # Retrieve all users from the database
    users = await session.execute(select(User))
    users = users.scalars().all()

    # Convert the User objects to dictionaries
    users_dicts = [
        {
            "id": user.id,
            "fullname": user.fullname,
            "email": user.email,
            "avatar": user.avatar,
        }
        for user in users
    ]

    return users_dicts








if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)