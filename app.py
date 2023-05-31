import asyncio
from sqlalchemy import  select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt, json
from datetime import datetime, timedelta
from models import User
from schemas import CreateCvRequest,CreateUserRequest,CreateDesignRequest,CreateCvDesignUserRequest,UserLoginRequest,UpdateCvRequest,UpdateUserRequest,UpdateCvDesignUserRequest,UpdateDesignRequest
import json
import uvicorn

from models import Cv,User,Design,CvDesignUser

from fastapi.middleware.cors import CORSMiddleware
from models import Base

from dotenv import load_dotenv

import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with the appropriate origin(s) for your React application
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



#register user
@app.post("/register")
async def register_user(user_request: CreateUserRequest, session: AsyncSession = Depends(get_session)):
    # Check if the user already exists in the database
    user = await session.execute(select(User).where(User.email == user_request.email))
    if user.scalar():
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_password = pwd_context.hash(user_request.hashed_password)

    # Create a new User object
    new_user = User(fullname=user_request.fullname, email=user_request.email,avatar=user_request.avatar, hashed_password=hashed_password)

    # Add the new user to the database
    session.add(new_user)
    await session.commit()

    return {"message": "User registered successfully"}


# login users
@app.post("/login")
async def login_user(user_request: UserLoginRequest, session: AsyncSession = Depends(get_session)):
    # Retrieve the user from the database
    user = await session.execute(select(User).where(User.email == user_request.email))
    user = user.scalar()

    if not user or not pwd_context.verify(user_request.hashed_password, user.hashed_password): # type: ignore
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate a JWT token
    token = generate_token(user.email) # type: ignore

    return {"token": token} 


def generate_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),

    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token 

#protected routes only for valid users
@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security),session: AsyncSession = Depends(get_session)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = await session.execute(select(User).where(User.email == email))
        cv = await session.execute(select(Cv).where(Cv.user_id == User.id))
        user = user.scalar()
        cv = cv.scalar()
        return {"id":user.id,"fullname":user.fullname,"email":user.email,"avatar":user.avatar,
                "userResumes":cv}
        # Perform additional authorization checks if necessary
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.exceptions.DecodeError, jwt.exceptions.InvalidSignatureError):
        raise HTTPException(status_code=401, detail="Invalid token")



#Get Users
@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    # Retrieve all users from the database
    users = await session.execute(select(User))
    user_list = users.scalars().all()

    return {"users": user_list}


#Get Single User
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    async with async_session() as session: # type: ignore
        db_user = await session.get(User, user_id)
        if db_user:
            return {"user_id": db_user.id,"fullname":db_user.fullname,"email": db_user.email, "hashed_password": db_user.hashed_password}
        else:
            return {"message": "User not found"}

#delete user
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    async with async_session() as session: # type: ignore
        delete_query = User.__table__.delete().where(User.id == user_id)
        result = await session.execute(delete_query)
        if result.rowcount > 0:
            await session.commit()
            return {"message": "User deleted successfully"}
        else:
            return {"message": "User not found"}

#update user
@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UpdateUserRequest):
    async with async_session() as session: # type: ignore
        db_user = await session.get(User, user_id)
        if db_user:
            db_user.fullname = user.fullname
            db_user.email = user.email
            db_user.avatar = user.avatar
            await session.commit()
            return {"message": "User updated successfully"}
        else:
            return {"message": "User not found"}


#create user cv
@app.post("/cvs/{user_id}")
async def create_user_cv(user_id: int, cv: CreateCvRequest):
    async with async_session() as session:  # type: ignore
        
        user = await session.get(User, user_id)
        if user:
            db_cv = cv.dict(exclude_none=True)
            db_cv["experiences"] = json.dumps(cv.experiences)  # Convert experiences to JSON
            db_cv["education"] = json.dumps(cv.education) 
            db_cv["languages"] = json.dumps(cv.languages) 
            db_cv["user_id"] = user_id
            cond = Cv(**db_cv)
            session.add(cond)
            await session.commit()
            return {"message": "Cv created successfully"}
        else: 
            return {"message": "User not found"}


# Get user CV
@app.get("/cvs/{user_id}")
async def get_user_cv(user_id: int):
    async with async_session() as session:
        query = select(Cv).where(Cv.user_id == user_id)
        result = await session.execute(query)
        cv_list = result.scalars().all()

        if cv_list:
            cv_data = []
            for cv in cv_list:
                experiences = cv.experiences
                education = cv.education
                languages = cv.languages
                try:
                    experiences = json.loads(cv.experiences)
                    education = json.loads(cv.education)
                    languages = json.loads(cv.languages)
                except json.JSONDecodeError:
                    # Handle JSON decode error if necessary
                    pass

                cv_data.append({
                    "user_id": cv.user_id,
                    "nom": cv.nom,
                    "prenom":cv.prenom,
                    "address":cv.address,
                    "email":cv.email,
                    "city":cv.city,
                    "country":cv.country,
                    "postalcode":cv.postalcode,
                    "tele":cv.tele,
                    "brief":cv.brief,
                    "img_url":cv.img_url,
                    "experiences": experiences,
                    "education": education,
                    "languages": languages
                })

            return cv_data
        else:
            return {"message": "CV not found"}




# Delete user CV
@app.delete("/users/{user_id}/cvs/{cv_id}")
async def delete_user_cv(user_id: int, cv_id: int):
    async with async_session() as session: # type: ignore
        user = await session.get(User, user_id)
        if user:
            db_cv = await session.get(Cv, cv_id)
            if db_cv:
                await session.delete(db_cv)  # Await the coroutine
                await session.commit()
                return {"message": "Cv deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Cv not found")
        else:
            raise HTTPException(status_code=404, detail="User not found")


#Update user cv
@app.put("/users/{user_id}/cvs/{cv_id}")
async def update_user_cv(user_id: int, cv_id: int, cv: UpdateCvRequest):
    async with async_session() as session: # type: ignore
        user = await session.get(User, user_id)
        if user:
            db_cv = await session.get(Cv, cv_id)
            if db_cv:
                db_cv.nom = cv.nom
                db_cv.prenom = cv.prenom
                db_cv.address = cv.address
                db_cv.email = cv.email
                db_cv.city = cv.city
                db_cv.country = cv.country
                db_cv.postalcode = cv.postalcode
                db_cv.tele = cv.tele
                db_cv.brief = cv.brief
                db_cv.img_url = cv.img_url
                db_cv.experiences = cv.experiences
                db_cv.education = cv.education
                db_cv.languages = cv.languages
                await session.commit()
                return {"message": "Cv updated successfully"}
            else:
                return {"message": "Cv not found"}       
        else:
            return {"message": "User not found"}








#create a new design and get design 
@app.post("/design")
async def create_design(design_data: CreateDesignRequest):
    async with async_session() as session:
        # Create a new design instance with the provided data
        new_design = Design(name=design_data.name)

        # Add the design to the session
        session.add(new_design)
        await session.commit()
        await session.refresh(new_design)

        # Return the created design
        return new_design
    
#get design
@app.get("/design/{design_id}")
async def get_design(design_id: int):
    async with async_session() as session:
        # Retrieve the design from the database
        design = await session.get(Design, design_id)

        # If the design doesn't exist, raise an HTTP exception
        if design is None:
            raise HTTPException(status_code=404, detail="Design not found")

        # Return the retrieved design
        return design

# Update Design
@app.put("/design/{design_id}")
async def update_design(design_id: int, design_data: UpdateDesignRequest, session: AsyncSession = Depends(get_session)):
    # Retrieve the design from the database
    design = await session.get(Design, design_id)

    # If the design doesn't exist, raise an HTTP exception
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")

    # Update the design with the provided data
    design.name = design_data.name

    # Commit the changes to the database
    await session.commit()

    # Return a success message
    return {"message": "Design updated successfully"}


# Delete Design
@app.delete("/design/{design_id}")
async def delete_design(design_id: int):
    async with async_session() as session: # type: ignore
        delete_query = Design.__table__.delete().where(Design.id == design_id)
        result = await session.execute(delete_query)
        if result.rowcount > 0:
            await session.commit()
            return {"message": "Design deleted successfully"}
        else:
            return {"message": "Design not found"}




# creating a new CvDesignUser
@app.post("/cvdesignusers/{cv_id}/{user_id}/{design_id}")
async def create_cv_design_user(cv_id: int, user_id: int, design_id: int, request: CreateCvDesignUserRequest, session: AsyncSession = Depends(get_session)):
    # Check if the CV exists
    cv = await session.get(Cv, cv_id)
    if cv is None:
        raise HTTPException(status_code=404, detail="CV not found")

    # Check if the User exists
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the Design exists
    design = await session.get(Design, design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")

    # Create a new CvDesignUser object with the provided data
    new_cv_design_user = CvDesignUser(
        cv_id=cv_id,
        user_id=user_id,
        design_id=design_id
    )

    # Add the new CvDesignUser to the database
    session.add(new_cv_design_user)
    await session.commit()
    await session.refresh(new_cv_design_user)

    # Return a success message
    return {"message": "CvDesignUser created successfully"}


# GET CvDesignUser
@app.get("/cvdesignusers/{cv_design_user_id}")
async def get_cv_design_user(cv_design_user_id: int, session: AsyncSession = Depends(get_session)):
    # Retrieve the CvDesignUser from the database
    cv_design_user = await session.get(CvDesignUser, cv_design_user_id)
    user_data = await session.execute(select(User).where(User.id == cv_design_user.user_id))
    cv_data = await session.execute(select(Cv).where(Cv.id == cv_design_user.cv_id))
    design_data = await session.execute(select(Design).where(Design.id == cv_design_user.design_id))
    user_data = user_data.scalar()
    cv_data = cv_data.scalar()
    design_data = design_data.scalar()
    # If the CvDesignUser doesn't exist, raise an HTTP exception
    if cv_design_user is None:
        raise HTTPException(status_code=404, detail="CvDesignUser not found")

    # Return the retrieved CvDesignUser
    return {user_data,cv_data,design_data}


# Update CvDesignUser
@app.put("/cvdesignusers/{cv_design_user_id}")
async def update_cv_design_user(cv_design_user_id: int, request: UpdateCvDesignUserRequest, session: AsyncSession = Depends(get_session)):
    # Retrieve the CvDesignUser from the database
    cv_design_user = await session.get(CvDesignUser, cv_design_user_id)

    # If the CvDesignUser doesn't exist, raise an HTTP exception
    if cv_design_user is None:
        raise HTTPException(status_code=404, detail="CvDesignUser not found")

    # Update the CvDesignUser with the provided data
    cv_design_user.cv_id = request.cv_id
    cv_design_user.user_id = request.user_id
    cv_design_user.design_id = request.design_id

    # Commit the changes to the database
    await session.commit()

    # Return a success message
    return {"message": "CvDesignUser updated successfully"}


# Delete CvDesignUser
@app.delete("/cvdesignusers/{cv_design_user_id}")
async def delete_cv_design_user(cv_design_user_id: int):
    async with async_session() as session: # type: ignore
        delete_query = CvDesignUser.__table__.delete().where(CvDesignUser.id == cv_design_user_id)
        result = await session.execute(delete_query)
        if result.rowcount > 0:
            await session.commit()    
            return {"message": "UserCvDesign deleted successfully"}
        else:
            return {"message": "UserCvDesign not found"}




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)