import asyncio
import itsdangerous
from sqlalchemy import  select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from passlib.context import CryptContext
import os
import requests
from fastapi.encoders import jsonable_encoder
import boto3
from starlette.responses import StreamingResponse
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from botocore.exceptions import NoCredentialsError
from fastapi import UploadFile,File
import jwt, json
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
from models import User
from schemas import CreateCvRequest,CreatePublicCvRequest,UpdatePublicCvRequest,CvPublicResponse,CreateUserRequest,UserLoginRequest,UpdateCvRequest,UpdateUserRequest,UserResponse,CreateLetterRequest,UpdateLetterRequest,UpdateCurrentUser,UpdatePasswordRequest,CreatePublicLetterRequest,UpdatePublicLetterRequest
import json
import uvicorn
import random
from models import Cv,User, Letter,PublicCv,PublicLetter,DeletedcCv,DeletedLetter
from fastapi.middleware.cors import CORSMiddleware
from models import Base
from starlette.config import Config
from starlette.requests import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse,RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from letter_generator import generate_cover_letter,limitLetterGenerator
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
from starlette.exceptions import HTTPException
import smtplib
from email.mime.text import MIMEText
import os
from httpx import AsyncClient  # Import the AsyncClient class from httpx for asynchronous requests



load_dotenv()

app = FastAPI()




app.add_middleware(SessionMiddleware, secret_key="!secret")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize the rate limiter
limiter = FastAPILimiter()

config = Config('.env')
oauth = OAuth(config)

# Configure your Google OAuth2 client credentials
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_BASE = os.environ.get('DB_BASE')


EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL = os.environ.get('EMAIL')

DIGITALOCEAN_SPACES_ACCESS_KEY = os.environ.get('DIGITALOCEAN_SPACES_ACCESS_KEY')
DIGITALOCEAN_SPACES_SECRET_KEY = os.environ.get('DIGITALOCEAN_SPACES_SECRET_KEY')
DIGITALOCEAN_SPACES_ENDPOINT_URL = os.environ.get('DIGITALOCEAN_SPACES_ENDPOINT_URL')
DIGITALOCEAN_SPACES_NAME = os.environ.get('DIGITALOCEAN_SPACES_NAME')

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_BASE}"
#DATABASE_URL = f"mysql+aiomysql://root@localhost:3306/cv_magique"
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False) # type: ignore

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    # Attach the rate limiter to the app
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
'''
@app.get("/")
async def welcome_api():
    return "this is a backend api of cvmagique"
'''


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


############################# AUTHENTICATION ##############################

@app.post("/register", status_code=201)
async def register_user(request: CreateUserRequest, session: AsyncSession = Depends(get_session)):
    # Check if the email is already registered
    existing_user = await session.execute(select(User).where(User.email == request.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà enregistré")

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
    message = f"Utilisateur créé avec succès"
    return {"message":message}

@app.post("/login")
async def login_user(request: UserLoginRequest, session: AsyncSession = Depends(get_session)):
    # Check if the user exists
    user = await session.execute(select(User).where(User.email == request.email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")

    # Verify the password
    if not verify_password(request.hashed_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")

    # Generate the access token
    access_token = create_access_token(user.id)

    # Return the access token
    return {"access_token": access_token, "token_type": "bearer"}

#Get Current User
@app.get("/me")
async def get_current_user(session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the current user from the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Create a dictionary from the user object
    user_dict = {
        "fullname": user.fullname,
        "email": user.email,
        "avatar": user.avatar,
        "is_admin":user.is_admin,
        "is_tutorial":user.is_tutorial
    }

    # Return the user data
    return user_dict

#update current user
@app.put("/me")
async def update_current_user(user_update: UpdateCurrentUser, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the current user from the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Update user information
    user.fullname = user_update.fullname
    user.is_active = user_update.is_active
    user.hashed_password = hash_password(user_update.hashed_password)
    
    # Commit the changes to the database
    await session.commit()

    # Return the updated user data
    
    return {"msg":"Les informations de votre profil ont été mises à jour avec succès"}


# Update password
@app.put("/me/update-password")
async def update_password(password_update: UpdatePasswordRequest, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the current user from the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Verify the current password
    if not verify_password(password_update.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Mot de passe actuel invalide")
  
    # Update the password
    user.hashed_password = hash_password(password_update.new_password)
    user.fullname = password_update.fullname
     
    # Commit the changes to the database
    await session.commit()

    return {"message": "Informations mises à jour avec succès"}



# this function is to parse data in json if it's in valid format and to keep as it is if it's string
def try_json_loads(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
    
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
            "img_blob": cv.img_blob,
            "style": cv.style,
            "color": cv.color,
            "description": cv.description,
            "experiences": try_json_loads(cv.experiences),
            "education": try_json_loads(cv.education),
            "languages": try_json_loads(cv.languages),
            "skills": try_json_loads(cv.skills),
            "loisirs": try_json_loads(cv.loisirs),
            "is_experiences":cv.is_experiences,
            "is_education":cv.is_education,
            "is_languages":cv.is_languages,
            "is_education":cv.is_education,
            "is_skills":cv.is_skills,
            "is_loisirs":cv.is_loisirs,
            "is_active":cv.is_active,
            "text_size":cv.text_size,
            "category_size":cv.category_size,
            "description_size":cv.description_size,
            "right_cate":cv.right_cate,
            "permis" :cv.permis, 
            "formatting" :try_json_loads(cv.formatting), 
            "left_cate":cv.left_cate,
            "user_id": cv.user_id
        }
       
        
        cvs_dicts.append(cv_dict)

    # Return the CV data
    return cvs_dicts

################### Images Handling #######################

# import cv image
@app.post("/me/cvs/{cv_id}/image")
async def import_cv_image(
    cv_id: str,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Save the uploaded image to DigitalOcean Spaces
    image_path = f"cvmagic/{cv_id}_{image.filename}"
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
            aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
        )
        s3.upload_fileobj(
            image.file,
            DIGITALOCEAN_SPACES_NAME,
            image_path,
            ExtraArgs={"ACL": "public-read"}
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")

    # Update the CV's image URL in the database
    cv = await session.execute(select(Cv).where(Cv.id == cv_id and Cv.user_id == user_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    cv.img_url = f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/{image_path}"
    await session.commit()
    response = requests.get(cv.img_url, stream=True)
    # Return a success message
    return StreamingResponse(response.iter_content(chunk_size=1024), media_type="image/png")

# GET CV image
@app.get("/me/cvs/{cv_id}/image")
async def get_cv_image(
    cv_id: str,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV from the database
    cv = await session.execute(select(Cv).where(Cv.id == cv_id and Cv.user_id == user_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Send a request to the CV's image URL and return it as a streaming response
    try:
        response = requests.get(cv.img_url, stream=True)
        return StreamingResponse(response.iter_content(chunk_size=1024), media_type="image/png")
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Failed to retrieve CV image")
    
# GET CV image url
@app.get("/me/cvs/{cv_id}/image/url")
async def get_cv_image(
    cv_id: str,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV from the database
    cv = await session.execute(select(Cv).where(Cv.id == cv_id and Cv.user_id == user_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Return the CV's image URL
    return {"img_url": cv.img_url}

################## public cv images functionalities #################
# import cv image
@app.post("/api/cvs/{cv_id}/image")
async def import_cv_image(
    cv_id: str,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    # Save the uploaded image to DigitalOcean Spaces
    image_path = f"cvmagic/{cv_id}_{image.filename}"
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
            aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
        )
        s3.upload_fileobj(
            image.file,
            DIGITALOCEAN_SPACES_NAME,
            image_path,
            ExtraArgs={"ACL": "public-read"}
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")

    # Update the CV's image URL in the database
    cv = await session.execute(select(PublicCv).where(PublicCv.id == cv_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    cv.img_url = f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/{image_path}"
    await session.commit()
    response = requests.get(cv.img_url, stream=True)
    # Return a success message
    return StreamingResponse(response.iter_content(chunk_size=1024), media_type="image/png")

# GET CV image
@app.get("/api/cvs/{cv_id}/image")
async def get_cv_image(
    cv_id: str,
    session: AsyncSession = Depends(get_session)
):
    # Retrieve the CV from the database
    cv = await session.execute(select(PublicCv).where(PublicCv.id == cv_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Send a request to the CV's image URL and return it as a streaming response
    try:
        response = requests.get(cv.img_url, stream=True)
        return StreamingResponse(response.iter_content(chunk_size=1024), media_type="image/png")
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Failed to retrieve CV image")

# GET CV image url
@app.get("/api/cvs/{cv_id}/image/url")
async def get_cv_image_url(
    cv_id: str,
    session: AsyncSession = Depends(get_session)
):
    # Retrieve the CV from the database
    cv = await session.execute(select(PublicCv).where(PublicCv.id == cv_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Return the CV's image URL
    return {"img_url": cv.img_url}

# delete cv image
@app.delete("/api/cvs/{cv_id}/image")
async def delete_cv_image(
    cv_id: str,
    session: AsyncSession = Depends(get_session)
):
    # Retrieve the CV from the database
    cv = await session.execute(select(PublicCv).where(PublicCv.id == cv_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Delete the CV image from DigitalOcean Spaces
    image_path = cv.img_url.replace(f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/", "")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
            aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
        )
        s3.delete_object(Bucket=DIGITALOCEAN_SPACES_NAME, Key=image_path)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")

    # Clear the CV's image URL in the database
    cv.img_url = None
    await session.commit()

    # Return a success message
    return {"message": "CV image deleted successfully"}


# delete cv image
@app.delete("/me/cvs/{cv_id}/image")
async def delete_cv_image(
    cv_id: str,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV from the database
    cv = await session.execute(select(Cv).where(Cv.id == cv_id and Cv.user_id == user_id))
    cv = cv.scalar()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Delete the CV image from DigitalOcean Spaces
    image_path = cv.img_url.replace(f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/", "")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
            aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
        )
        s3.delete_object(Bucket=DIGITALOCEAN_SPACES_NAME, Key=image_path)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")

    # Clear the CV's image URL in the database
    cv.img_url = None
    await session.commit()

    # Return a success message
    return {"message": "CV image deleted successfully"}


#generate random id
def generate_random_id(length=10):
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

#create user cv
@app.post("/me/cvs")
async def create_cv(cv: CreateCvRequest, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]
    cv_id = generate_random_id()
    # Create a new CV object from the request data
    db_cv = cv.dict(exclude_none=True)
    db_cv["id"] = cv_id
    db_cv["experiences"] = json.dumps(cv.experiences)  # Convert experiences to JSON
    db_cv["education"] = json.dumps(cv.education) 
    db_cv["languages"] = json.dumps(cv.languages) 
    db_cv["skills"] = json.dumps(cv.skills) 
    db_cv["loisirs"] = json.dumps(cv.loisirs) 
    db_cv["formatting"] = json.dumps(cv.formatting) 
    db_cv["user_id"] = user_id
    cv = Cv(**db_cv)
    
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

#duplicate cv
@app.post("/me/cvs/duplicate/{cv_id}")
async def duplicate_cv(cv_id: str, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV to be duplicated
    cv = await session.get(Cv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Check if the CV belongs to the current user
    if cv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Create a new CV object with the same data as the original CV
    new_cv = Cv(
        id=generate_random_id(),
        nom=cv.nom,
        prenom=cv.prenom,
        address=cv.address,
        email=cv.email,
        city=cv.city,
        country=cv.country,
        postalcode=cv.postalcode,
        tele=cv.tele,
        brief=cv.brief,
        img_url="",
        img_blob="",
        style=cv.style,
        color=cv.color,
        description=cv.description,
        experiences=cv.experiences,
        education=cv.education,
        languages=cv.languages,
        skills=cv.skills,
        loisirs=cv.loisirs,
        is_experiences=cv.is_experiences,
        is_education=cv.is_education,
        is_languages=cv.is_languages,
        is_skills=cv.is_skills,
        is_loisirs=cv.is_loisirs,
        is_active = cv.is_active,
        text_size = cv.text_size,
        category_size=cv.category_size,
        description_size=cv.description_size,
        right_cate = cv.right_cate,
        permis=cv.permis,
        formatting =cv.formatting, 
        left_cate = cv.left_cate,
        user_id=user_id
    )

    # Save the new CV to the database
    session.add(new_cv)
    await session.commit()

    # Return the duplicated CV
    return {"cv": new_cv, "message": "CV duplicated successfully"}


#update cv 
@app.put("/me/cvs/{cv_id}")
async def update_cv(cv_id: str, cv_data: UpdateCvRequest, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    current_user_id = payload["user_id"]

    # Retrieve the CV to be updated
    cv = await session.get(Cv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Check if the current user has permission to update their own CV
    if current_user_id != cv.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Update the CV with the provided data
    for field, value in cv_data.dict(exclude_unset=True).items():
        setattr(cv, field, value)

    # Commit the changes to the database
    await session.commit()

    # Return the updated CV
    return {"cv": cv, "message": "CV updated successfully"}



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
    
    # Delete the CV image from DigitalOcean Spaces (if it exists)
    if cv.img_url:
        image_path = cv.img_url.replace(f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/", "")
        try:
            s3 = boto3.client(
                "s3",
                endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
                aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
                aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
            )
            s3.delete_object(Bucket=DIGITALOCEAN_SPACES_NAME, Key=image_path)
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")
    
    
    # Delete the CV from the database
    deleted_cv = DeletedcCv(
        id=cv.id,
        nom=cv.nom,
        prenom=cv.prenom,
        address=cv.address,
        email=cv.email,
        city=cv.city,
        country=cv.country,
        postalcode=cv.postalcode,
        tele=cv.tele,
        brief=cv.brief,
        img_url="",
        img_blob="",
        style=cv.style,
        color=cv.color,
        description=cv.description,
        experiences=cv.experiences,
        education=cv.education,
        languages=cv.languages,
        skills=cv.skills,
        loisirs=cv.loisirs,
        is_experiences=cv.is_experiences,
        is_education=cv.is_education,
        is_languages=cv.is_languages,
        is_skills=cv.is_skills,
        is_loisirs=cv.is_loisirs,
        is_active = cv.is_active,
        text_size = cv.text_size,
        category_size=cv.category_size,
        description_size=cv.description_size,
        right_cate = cv.right_cate,
        permis =cv.permis, 
        formatting =cv.formatting, 
        left_cate = cv.left_cate,
        user_id=user_id
    )
    session.add(deleted_cv)
    await session.delete(cv)
    await session.commit()
    
    # Return a success message
    return {"message": "CV deleted successfully"}

###################  Public CV Functionality ######################
# Create public user CV
@app.post("/api/cvs")
async def create_cv(cv: CreatePublicCvRequest, session: AsyncSession = Depends(get_session)):
    # Generate a CV ID
    cv_id = generate_random_id()

    # Create a new CV object from the request data
    db_cv = cv.dict(exclude_none=True)
    db_cv["id"] = cv_id
    db_cv["experiences"] = json.dumps(cv.experiences)  # Convert experiences to JSON
    db_cv["education"] = json.dumps(cv.education) 
    db_cv["languages"] = json.dumps(cv.languages) 
    db_cv["skills"] = json.dumps(cv.skills) 
    db_cv["loisirs"] = json.dumps(cv.loisirs) 
    db_cv["formatting"] = json.dumps(cv.formatting) 
    cv = PublicCv(**db_cv)
    
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

# Get CV by ID
@app.get("/api/cvs/{cv_id}")
async def get_cv(cv_id: str, session: AsyncSession = Depends(get_session)):
    # Retrieve the CV from the database
    cv = await session.get(PublicCv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Return the CV
    cv_info = {
            "id": cv_id,
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
            "img_blob": cv.img_blob,
            "style": cv.style,
            "color": cv.color,
            "description": cv.description,
            "experiences": try_json_loads(cv.experiences),
            "education": try_json_loads(cv.education),
            "languages": try_json_loads(cv.languages),
            "skills": try_json_loads(cv.skills),
            "loisirs": try_json_loads(cv.loisirs),
            "is_experiences":cv.is_experiences,
            "is_education":cv.is_education,
            "is_languages":cv.is_languages,
            "is_education":cv.is_education,
            "is_skills":cv.is_skills,
            "is_loisirs":cv.is_loisirs,
            "is_active":cv.is_active,
            "text_size":cv.text_size,
            "category_size":cv.category_size,
            "description_size":cv.description_size,
            "right_cate":cv.right_cate,
            "permis" :cv.permis, 
            "formatting" :try_json_loads(cv.formatting), 
            "left_cate":cv.left_cate,
        }
    return {"cv": cv_info}

#assigned public cv to a user
@app.post("/api/cvs/copycv/{cv_id}")
async def copy_cv(cv_id: str, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the CV to be duplicated
    cv = await session.get(PublicCv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
   

    # Create a new CV object with the same data as the original CV
    new_cv = Cv(
        id=cv_id,
        nom=cv.nom,
        prenom=cv.prenom,
        address=cv.address,
        email=cv.email,
        city=cv.city,
        country=cv.country,
        postalcode=cv.postalcode,
        tele=cv.tele,
        brief=cv.brief,
        img_url=cv.img_url,
        img_blob=cv.img_blob,
        style=cv.style,
        color=cv.color,
        description=cv.description,
        experiences=cv.experiences,
        education=cv.education,
        languages=cv.languages,
        skills=cv.skills,
        loisirs=cv.loisirs,
        is_experiences=cv.is_experiences,
        is_education=cv.is_education,
        is_languages=cv.is_languages,
        is_skills=cv.is_skills,
        is_loisirs=cv.is_loisirs,
        is_active = cv.is_active,
        text_size = cv.text_size,
        category_size=cv.category_size,
        description_size=cv.description_size,
        right_cate = cv.right_cate,
        permis =cv.permis, 
        formatting =cv.formatting, 
        left_cate = cv.left_cate,
        user_id=user_id
    )

    # Save the new CV to the database
    session.add(new_cv)
    await session.delete(cv)
    await session.commit()

    # Return the duplicated CV
    return {"cv": new_cv, "message": "CV assigned to user successfully"}


# Update CV
@app.put("/api/cvs/{cv_id}")
async def update_cv(cv_id: str, cv_data: UpdatePublicCvRequest, session: AsyncSession = Depends(get_session)):
    # Retrieve the CV to be updated
    cv = await session.get(PublicCv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Update the CV with the provided data
    for field, value in cv_data.dict(exclude_unset=True).items():
        setattr(cv, field, value)

    # Commit the changes to the database
    await session.commit()

    # Return the updated CV
    return {"cv": cv, "message": "CV updated successfully"}


# Delete CV
@app.delete("/api/cvs/{cv_id}")
async def delete_cv(cv_id: str, session: AsyncSession = Depends(get_session)):
    # Retrieve the CV from the database
    cv = await session.get(PublicCv, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Delete the CV from the database
    await session.delete(cv)
    await session.commit()

    # Return a success message
    return {"message": "CV deleted successfully"}


####################### ADMIN CRUD #################################

#get users
@app.get("/admin/users", response_model=List[UserResponse])
async def get_all_users_as_admin(session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the current user from the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the current user is an admin
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Retrieve all users from the database
    users = await session.execute(select(User))
    users = users.scalars().all()

    # Create a list of UserResponse objects
    user_responses = [
        UserResponse(
            id=user.id,
            fullname=user.fullname,
            email=user.email,
            avatar=user.avatar,
            is_admin=user.is_admin,
            is_active=user.is_active
        )
        for user in users
    ]

    return user_responses


@app.put("/admin/users/{user_id}")
async def update_user_as_admin(
    user_id: int,
    user_data: UpdateUserRequest,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    admin_user_id = payload["user_id"]

    # Retrieve the admin user from the database
    admin_user = await session.execute(select(User).where(User.id == admin_user_id))
    admin_user = admin_user.scalar_one_or_none()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found")
     
    # Check if the admin user is an admin
    if not admin_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Retrieve the user to be updated
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the user with the provided data
    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    # Commit the changes to the database
    await session.commit()

    # Return the updated user
    return {"user":user,"message":"user updated successfully"}


@app.delete("/admin/users/{user_id}")
async def delete_user_as_admin(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    admin_user_id = payload["user_id"]

    # Retrieve the admin user from the database
    admin_user = await session.execute(select(User).where(User.id == admin_user_id))
    admin_user = admin_user.scalar_one_or_none()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Check if the admin user is an admin
    if not admin_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Retrieve the user to be deleted
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user from the database
    await session.delete(user)
    await session.commit()

    # Return a success message
    return {"message": "User deleted successfully"}




#Get all the cvs in the database
@app.get("/admin/cvs")
async def get_all_cvs(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    admin_user_id = payload["user_id"]

    # Retrieve the admin user from the database
    admin_user = await session.execute(select(User).where(User.id == admin_user_id))
    admin_user = admin_user.scalar_one_or_none()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Check if the admin user is an admin
    if not admin_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Retrieve all CVs
    cvs = await session.execute(select(Cv))
    
    cvs = cvs.scalars().all()
    cvs_dicts = []
    for cv in cvs:
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
            "img_blob": cv.img_blob,
            "style": cv.style,
            "color": cv.color,
            "description":cv.description,
            "experiences": json.loads(cv.experiences),
            "education": json.loads(cv.education),
            "languages": json.loads(cv.languages),
            "skills":json.loads(cv.skills),
            "loisirs": json.loads(cv.loisirs),
            "is_experiences": cv.is_experiences,
            "is_education": cv.is_education,
            "is_languages": cv.is_languages,
            "is_skills":cv.is_skills,
            "is_loisirs": cv.is_loisirs,
            "is_active":cv.is_active,
            "text_size":cv.text_size,
            "category_size":cv.category_size,
            "description_size":cv.description_size,
            "right_cate":cv.right_cate,
            "permis" :cv.permis, 
            "formatting" :json.loads(cv.formatting), 
            "left_cate":cv.left_cate,
            "user_id": cv.user_id
        }
        cv_dict['experiences'] = json.loads(cv_dict['experiences'])
        cv_dict['education'] = json.loads(cv_dict['education'])
        cv_dict['languages'] = json.loads(cv_dict['languages'])
        cv_dict['skills'] = json.loads(cv_dict['skills'])
        cv_dict['loisirs'] = json.loads(cv_dict['loisirs'])
        cvs_dicts.append(cv_dict)
    # Return the list of CVs
    return cvs_dicts






########### Letters  CRUD #####################
@app.post("/me/letters")
async def create_letter(letter: CreateLetterRequest, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]
    letter_id = generate_random_id()
    
    # Create a new Letter object from the request data
    db_letter = letter.dict(exclude_none=True)
    db_letter["id"] = letter_id
    db_letter["user_id"] = user_id
    db_letter["formatting"] = json.dumps(letter.formatting) 
    letter = Letter(**db_letter)
    
    # Save the new letter to the database
    session.add(letter)
    await session.commit()

    # Create a success message
    message = f"Letter with ID {letter.id} created successfully"

    # Return the created letter and the success message as a response
    return {
        "letter": letter,
        "message": message
    }

@app.post("/me/letters/duplicate/{letter_id}")
async def duplicate_letter(letter_id: str, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the letter to be duplicated
    letter = await session.get(Letter, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")

    # Check if the letter belongs to the current user
    if letter.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Create a new letter object with the same data as the original letter
    new_letter = Letter(
        id=generate_random_id(),
        a_prenom=letter.a_prenom,
        a_nom=letter.a_nom,
        a_email=letter.a_email,
        a_ville=letter.a_ville,
        a_adresse=letter.a_adresse,
        a_Code_postal=letter.a_Code_postal,
        a_tele=letter.a_tele,
        b_prenom=letter.b_prenom,
        b_nom=letter.b_nom,
        b_entreprise=letter.b_entreprise,
        b_ville=letter.b_ville,
        b_adresse=letter.b_adresse,
        b_Code_postal=letter.b_Code_postal,
        objet=letter.objet,
        date=letter.date,
        lieu=letter.lieu,
        style=letter.style,
        signature_alignement=letter.signature_alignement,
        signature_couleur=letter.signature_couleur,
        signature_taille=letter.signature_taille,
        signature_police=letter.signature_police,
        color=letter.color,
        lettre_de_motivation=letter.lettre_de_motivation,
        signature=letter.signature,
        formatting=letter.formatting, 
        is_active=letter.is_active,
        user_id=user_id
    )

    # Save the new letter to the database
    session.add(new_letter)
    await session.commit()

    # Return the duplicated letter
    return {"letter": new_letter, "message": "Letter duplicated successfully"}

@app.put("/me/letters/{letter_id}")
async def update_letter(letter_id: str, letter_data: UpdateLetterRequest, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    current_user_id = payload["user_id"]

    # Retrieve the letter to be updated
    letter = await session.get(Letter, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")

    # Check if the current user has permission to update their own letter
    if current_user_id != letter.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Update the letter with the provided data
    for field, value in letter_data.dict(exclude_unset=True).items():
        setattr(letter, field, value)

    # Commit the changes to the database
    await session.commit()

    # Return the updated letter
    return {"letter": letter, "message": "Letter updated successfully"}

@app.delete("/me/letters/{letter_id}")
async def delete_letter(
    letter_id: str,
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the letter from the database
    letter = await session.get(Letter, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")

    # Check if the letter belongs to the current user
    if letter.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Delete the letter from the database
    del_letter = DeletedLetter(
        id=letter.id,
        a_prenom=letter.a_prenom,
        a_nom=letter.a_nom,
        a_email=letter.a_email,
        a_ville=letter.a_ville,
        a_adresse=letter.a_adresse,
        a_Code_postal=letter.a_Code_postal,
        a_tele=letter.a_tele,
        b_prenom=letter.b_prenom,
        b_nom=letter.b_nom,
        b_entreprise=letter.b_entreprise,
        b_ville=letter.b_ville,
        b_adresse=letter.b_adresse,
        b_Code_postal=letter.b_Code_postal,
        objet=letter.objet,
        date=letter.date,
        lieu=letter.lieu,
        style=letter.style,
        signature_alignement=letter.signature_alignement,
        signature_couleur=letter.signature_couleur,
        signature_taille=letter.signature_taille,
        signature_police=letter.signature_police,
        color=letter.color,
        lettre_de_motivation="",
        signature=letter.signature,
        formatting = letter.formatting,
        is_active=letter.is_active,
        user_id=user_id
    )
    session.add(del_letter)
    await session.delete(letter)
    await session.commit()

    # Return a success message
    return {"message": "Letter deleted successfully"}

@app.get("/me/letters")
async def get_current_user_letters(session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the letters of the current user from the database
    letters = await session.execute(select(Letter).where(Letter.user_id == user_id))
    letters = letters.scalars().all()
    
    # Convert the letter objects to dictionaries
    letters_dicts = []
    for letter in letters:
        letter_dict = {
            "id": letter.id,
            "a_prenom": letter.a_prenom,
            "a_nom": letter.a_nom,
            "a_email": letter.a_email,
            "a_ville": letter.a_ville,
            "a_adresse": letter.a_adresse,
            "a_Code_postal": letter.a_Code_postal,
            "a_tele": letter.a_tele,
            "b_prenom": letter.b_prenom,
            "b_nom": letter.b_nom,
            "b_entreprise": letter.b_entreprise,
            "b_ville": letter.b_ville,
            "b_adresse": letter.b_adresse,
            "b_Code_postal": letter.b_Code_postal,
            "objet": letter.objet,
            "date": letter.date,
            "lieu": letter.lieu,
            "style":letter.style,
            "signature_alignement":letter.signature_alignement,
            "signature_couleur":letter.signature_couleur,
            "signature_taille":letter.signature_taille,
            "signature_police":letter.signature_police,
            "color":letter.color,
            "lettre_de_motivation": letter.lettre_de_motivation,
            "signature": letter.signature,
            "formatting" :try_json_loads(letter.formatting),
            "is_active": letter.is_active,
            "user_id": letter.user_id
        }
        letters_dicts.append(letter_dict)

    # Return the letter data
    return letters_dicts

########### Public Letters  CRUD #####################
#create public letter
@app.post("/api/letters")
async def create_public_letter(letter: CreatePublicLetterRequest, session: AsyncSession = Depends(get_session)):
    letter_id = generate_random_id()
    # Create a new Letter object from the request data
    db_letter = letter.dict(exclude_none=True)
    db_letter["id"] = letter_id
    db_letter["formatting"] = json.dumps(letter.formatting) 
    letter = PublicLetter(**db_letter)
    
    # Save the new letter to the database
    session.add(letter)
    await session.commit()
    
    # Create a success message
    message = f"Letter created successfully"

    # Return the created letter and the success message as a response
    return {
        "letter": letter,
        "message": message
    }

#Get Letter By ID
@app.get("/api/letter/{letter_id}")
async def get_public_letter(letter_id: str, session: AsyncSession = Depends(get_session)):
    # Retrieve the CV from the database
    letter = await session.get(PublicLetter, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="letter not found")

    # Return the CV
    letter_info = {
            "id": letter_id,
            "a_prenom": letter.a_prenom,
            "a_nom": letter.a_nom,
            "a_email": letter.a_email,
            "a_ville": letter.a_ville,
            "a_adresse": letter.a_adresse,
            "a_Code_postal": letter.a_Code_postal,
            "a_tele": letter.a_tele,
            "b_prenom": letter.b_prenom,
            "b_nom": letter.b_nom,
            "b_entreprise": letter.b_entreprise,
            "b_ville": letter.b_ville,
            "b_adresse": letter.b_adresse,
            "b_Code_postal": letter.b_Code_postal,
            "objet": letter.objet,
            "date": letter.date,
            "lieu": letter.lieu,
            "style":letter.style,
            "signature_alignement":letter.signature_alignement,
            "signature_couleur":letter.signature_couleur,
            "signature_taille":letter.signature_taille,
            "signature_police":letter.signature_police,
            "color":letter.color,
            "lettre_de_motivation": letter.lettre_de_motivation,
            "signature": letter.signature,
            "is_active": letter.is_active,
            "formatting" : try_json_loads(letter.formatting),
            "user_id": letter.user_id
        }
    return {"letter": letter_info }

#update public letter 
@app.put("/api/letter/{letter_id}")
async def update_public_letter(letter_id: str, letter_data: UpdatePublicLetterRequest, session: AsyncSession = Depends(get_session)):
   
    # Retrieve the letter to be updated
    letter = await session.get(PublicLetter, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")

    # Update the letter with the provided data
    for field, value in letter_data.dict(exclude_unset=True).items():
        setattr(letter, field, value)

    # Commit the changes to the database
    await session.commit()

    # Return the updated letter
    return {"letter": letter, "message": "Letter updated successfully"}


#assigned letter to user
@app.post("/api/letters/copyletter/{letter_id}")
async def copy_letter(letter_id: str, session: AsyncSession = Depends(get_session), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Retrieve the letter to be duplicated
    letter = await session.get(PublicLetter, letter_id)
    if not letter:
        raise HTTPException(status_code=404,detail="letter not found")
    # Create a new letter object with the same data as the original letter
    new_letter = Letter(
        id=letter_id,
        a_prenom=letter.a_prenom,
        a_nom=letter.a_nom,
        a_email=letter.a_email,
        a_ville=letter.a_ville,
        a_adresse=letter.a_adresse,
        a_Code_postal=letter.a_Code_postal,
        a_tele=letter.a_tele,
        b_prenom=letter.b_prenom,
        b_nom=letter.b_nom,
        b_entreprise=letter.b_entreprise,
        b_ville=letter.b_ville,
        b_adresse=letter.b_adresse,
        b_Code_postal=letter.b_Code_postal,
        objet=letter.objet,
        date=letter.date,
        lieu=letter.lieu,
        style=letter.style,
        signature_alignement=letter.signature_alignement,
        signature_couleur=letter.signature_couleur,
        signature_taille=letter.signature_taille,
        signature_police=letter.signature_police,
        color=letter.color,
        lettre_de_motivation=letter.lettre_de_motivation,
        signature=letter.signature,
        formatting = json.dumps(letter.formatting),
        is_active=letter.is_active,
        user_id=user_id
    )

    # Save the new letter to the database
    session.add(new_letter)
    await session.delete(letter)
    await session.commit()

    # Return the duplicated letter
    return {"letter": new_letter, "message": "Letter assigned to user successfully"}


########################## GOOGLE AUTHENTICATION ###########################

@app.get('/')
async def homepage(request: Request):
    return "cv magique API"


CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)



# @app.get('/google/login')
# async def login(request: Request):
#     redirect_uri = "http:localhost:3000/app"
#     google_uri = await oauth.google.authorize_redirect(request, redirect_uri)
#     return google_uri
    


# Redirect users to the Google OAuth2 authorization URL
@app.get("/google/login")
async def login():
    google_authorization_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=openid profile email"
    )
    return {"message": "Login via Google", "url": google_authorization_url}

@app.get("/login/callback")
async def callback(
    code: str = None,
    state: str = None,
    session: AsyncSession = Depends(get_session)
):
    try:
        if code is None:
            raise HTTPException(status_code=400, detail="Authorization code missing")

        google_token_url = "https://accounts.google.com/o/oauth2/token"
        client_id = GOOGLE_CLIENT_ID
        client_secret = GOOGLE_CLIENT_SECRET
        redirect_uri = REDIRECT_URI

        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with AsyncClient() as client:
            response = await client.post(google_token_url, data=token_data)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to obtain an access token")

        token_response = response.json()

        google_user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {
            "Authorization": f"Bearer {token_response['access_token']}"
        }

        async with AsyncClient() as client:
            user_info_response = await client.get(google_user_info_url, headers=headers)

        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            email = user_info.get('email')

            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalar()
            # return {'user': user}
            if user:
                # User already exists, log them in
                user_data = {
                    'id': user.id,
                    'fullname': user.fullname,
                    'email': user.email,
                    'avatar': user.avatar
                }
                access_token = create_access_token(user.id)
                return RedirectResponse(url=f'https://app.cvmagique.fr/login/callback?access_token={access_token}')
            else:
                # User does not exist, create a new user and save their information
                user = User(fullname=user_info.get('name'), email=email, avatar=user_info.get('picture'))
                session.add(user)
                await session.commit()

                user_data = {
                    'id': user.id,
                    'fullname': user.fullname,
                    'email': user.email,
                    'avatar': user.avatar
                }
                access_token = create_access_token(user.id)
                return RedirectResponse(url=f'https://app.cvmagique.fr/login/callback?access_token={access_token}')
        else:
            raise HTTPException(status_code=user_info_response.status_code, detail="Failed to fetch user info from Google")
    except Exception as e:
        print(f"Error in /login/callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# @app.get('/auth')
# async def auth(request: Request, session: AsyncSession = Depends(get_session)):
#     try:
#         token = await oauth.google.authorize_access_token(request)
#     except OAuthError as error:
#         return JSONResponse(content={'error': error.error})
    
#     user_info = token.get('userinfo')
#     if user_info:
#         email = user_info.get('email')
#         # Check if the user already exists in the database
#         stmt = select(User).where(User.email == email)
#         result = await session.execute(stmt)
#         user = result.scalar()

#         if user:
#             # User already exists, log them in
#             request.session['user'] = {'id': user.id, 'fullname': user.fullname, 'email': user.email, 'picture': user.avatar}
#             # Generate the access token
#             access_token = create_access_token(user.id)
#             return RedirectResponse(url=f'https://cvmagique.vercel.app/login?access_token={access_token}')

#         else:
#             # User does not exist, create a new user and save their information
#             user = User(fullname=user_info.get('name'), email=email, avatar=user_info.get('picture'))
#             session.add(user)
#             await session.commit()
            
#             request.session['user'] = {'id': user.id, 'fullname': user.fullname, 'email': user.email, 'avatar': user.avatar}

#             # Return token
#             access_token = create_access_token(user.id)
#             return RedirectResponse(url=f'https://app.cvmagique.fr/login?access_token={access_token}')

           
            

#     return JSONResponse(content={'message': 'User information not available'})

    

  


@app.get('/google/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return JSONResponse(content={'message': 'Logged out'})


############### Lettre generator with chatgpt ##############
@app.post("/generate_cover_letter/{company_name}/{subject}/{skills}/{nb_experience}/{activite}/{poste}")
async def generate_cover_letter_route(
    request: Request,
    company_name: str,
    subject: str,
    skills: str,
    nb_experience: int,
    activite: str,
    poste: str,
):
    await limitLetterGenerator(request)
    try:
        result = await generate_cover_letter(company_name, subject, nb_experience, activite, poste, skills)
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


########### RESET PASSWORD FUNCTINOALITY ###############

serializer = URLSafeTimedSerializer(SECRET_KEY)

def send_email(email: str, subject: str, body: str):
    sender = EMAIL
    receiver = email
    message = MIMEText(body, "html")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, EMAIL_PASSWORD)
        server.sendmail(sender, receiver, message.as_string())

@app.post("/reset-password", status_code=200)
async def reset_password(email: str,session: AsyncSession = Depends(get_session)):
    # Check if the user exists in the database
    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate the password reset token
    token = serializer.dumps(user.id)

    # Create the reset link
    reset_link = f"http://cvmagique.vercel.app/updatepassword?token={token}"

    # Create the email body
    subject = "Password Reset"
    # Read the email template file
    with open('email_template.html', 'r') as file:
        email_template = file.read()

   # Replace placeholders in the email template with actual values
    body = email_template.replace('{{fullname}}', user.fullname).replace('{{reset_link}}', reset_link)

    # Send the reset link to the user's email
    send_email(email, subject, body)

    return {"message": "Le lien de réinitialisation du mot de passe a été envoyé à votre adresse e-mail"}


@app.put("/reset-password", status_code=200)
async def update_password(reset_token: str, new_password: str,session: AsyncSession = Depends(get_session)):
    try:
        # Decrypt the reset token to get the user ID
        user_id = serializer.loads(reset_token, max_age=3600)  # Token expires after 1 hour

        # Retrieve the user from the database
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the user's password
        user.hashed_password = hash_password(new_password)
        await session.commit()

        return {"message": "Le mot de passe a été mis à jour avec succès"}
    except itsdangerous.exc.SignatureExpired:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    except itsdangerous.exc.BadSignature:
        raise HTTPException(status_code=400, detail="Invalid reset token")


# user images :

# import user image
@app.post("/me/profile/image")
async def import_user_image(
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Save the uploaded image to DigitalOcean Spaces
    image_path = f"cvmagic/{user_id}_{generate_random_id()}"
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
            aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
        )
        s3.upload_fileobj(
            image.file,
            DIGITALOCEAN_SPACES_NAME,
            image_path,
            ExtraArgs={"ACL": "public-read"}
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")

    # Update the USER's image URL in the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    user.avatar = f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/{image_path}"
    await session.commit()
    
    return {"message":"image upload successfuuly","avatar_url":user.avatar}


# delete user image
@app.delete("/me/profile/image")
async def delete_user_image(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
     # Decode the access token
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload["user_id"]
    # Retrieve the User from the database
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    # Delete the User image from DigitalOcean Spaces
    image_path = user.avatar.replace(f"{DIGITALOCEAN_SPACES_ENDPOINT_URL}/{DIGITALOCEAN_SPACES_NAME}/", "")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT_URL,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY,
            aws_secret_access_key=DIGITALOCEAN_SPACES_SECRET_KEY
        )
        s3.delete_object(Bucket=DIGITALOCEAN_SPACES_NAME, Key=image_path)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Failed to connect to DigitalOcean Spaces")

    # Clear the USER's image URL in the database
    user.avatar = None
    await session.commit()

    # Return a success message
    return {"message": "user image deleted successfully"}

 



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

        

   
