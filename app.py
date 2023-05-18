import asyncio
import sqlalchemy
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI
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
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=True, autoflush=False) # type: ignore

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

### the API CRUD ###
#API root
@app.get("/")
async def welcome_api():
    return "this is a backend api of cvmagique"

#get Candidats
@app.get("/candidats")
async def get_candidats():
    async with async_session() as session:  # type: ignore
        result = await session.execute(Candidat.__table__.select())
        candidats = result.fetchall()
        if candidats:
            candidats_list = [{
            "id": candidat.id, "nom": candidat.nom,
            "prenom": candidat.prenom, "address": candidat.address,
            "email": candidat.email, "city": candidat.city,
            "country": candidat.country, "postalcode": candidat.postalcode,
            "tele": candidat.tele, "skills": candidat.skills,
            "img_url": candidat.img_url  
            
            } for candidat in candidats]
            return {"candidats": candidats_list}
        else:
            return {"message": "Candidats not found"}



#create new candidat
@app.post("/candidats")
async def create_candidat(candidat: CreateCandidatRequest):
    async with async_session() as session: # type: ignore
        db_candidat = Candidat(
            nom=candidat.nom,
            prenom=candidat.prenom,
            address=candidat.address,
            email=candidat.email,
            city=candidat.city,
            country=candidat.country,
            postalcode=candidat.postalcode,
            tele=candidat.tele,
            skills=candidat.skills,
            img_url=candidat.img_url
        )
        session.add(db_candidat)
        await session.commit()
        return {"message": "Candidat created successfully"}

# Get candidat by ID
@app.get("/candidats/{candidat_id}")
async def get_candidat(candidat_id: int):
    async with async_session() as session: # type: ignore
        result = await session.execute(Candidat.__table__.select().where(Candidat.id == candidat_id))
        candidat = result.fetchone()
        if candidat:
            candidat_data = {
                "id": candidat.id, "nom": candidat.nom,
                "prenom": candidat.prenom, "address": candidat.address,
                "email": candidat.email, "city": candidat.city,
                "country": candidat.country, "postalcode": candidat.postalcode,
                "tele": candidat.tele, "skills": candidat.skills,
                "img_url": candidat.img_url
            }
            return {"candidat": candidat_data} 
        else:
            return {"message": "Candidat not found"}

# Update Candidat
@app.put("/candidats/{candidat_id}")
async def update_candidat(candidat_id: int, candidat: CreateCandidatRequest):
    async with async_session() as session: # type: ignore
        db_candidat = await session.get(Candidat, candidat_id)
        if db_candidat:
            db_candidat.nom = candidat.nom
            db_candidat.prenom = candidat.prenom
            db_candidat.address = candidat.address
            db_candidat.email = candidat.email
            db_candidat.city = candidat.city
            db_candidat.country = candidat.country
            db_candidat.postalcode = candidat.postalcode
            db_candidat.tele = candidat.tele
            db_candidat.skills = candidat.skills
            db_candidat.img_url = candidat.img_url
            await session.commit()
            return {"message": "Candidat updated successfully"}
        else:
            return {"message": "Candidat not found"}

    
# Delete candidat
@app.delete("/candidats/{candidat_id}")
async def delete_candidat(candidat_id: int):
    async with async_session() as session: # type: ignore
        delete_query = Candidat.__table__.delete().where(Candidat.id == candidat_id)
        result = await session.execute(delete_query)
        if result.rowcount > 0:
            await session.commit()
            return {"message": "Candidat deleted successfully"}
        else:
            return {"message": "Candidat not found"}

# Experience CRUD #

#Create a new Experience for a given User
@app.post("/candidats/{candidat_id}/experience")
async def create_candidat_experience(candidat_id: int, experience: CreateExperienceRequest):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            db_experience = Experience(
                candidat_id=candidat_id,
                societe=experience.societe,
                start_at=experience.start_at,
                end_at=experience.end_at,
                job=experience.job
            )
            session.add(db_experience)
            await session.commit()
            return {"message": "Experience created successfully"}
        else:
            return {"message": "Candidat not found"}

#retrieve experiences
@app.get("/candidats/{candidat_id}/experience")
async def get_candidat_experience(candidat_id: int):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            experiences = await session.execute(select(Experience).where(Experience.candidat_id == candidat_id))
            candidat_experiences = [dict(experience._asdict()) for experience in experiences]
            return {"experiences": candidat_experiences}
        else:
            return {"message": "Candidat not found"}

# Update user experience
@app.put("/candidats/{candidat_id}/experience/{experience_id}")
async def update_candidat_experience(candidat_id: int, experience_id: int, experience: CreateExperienceRequest):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            db_experience = await session.get(Experience, experience_id)
            if db_experience:
                db_experience.societe = experience.societe
                db_experience.start_at = experience.start_at
                db_experience.end_at = experience.end_at
                db_experience.job = experience.job
                await session.commit()
                return {"message": "Experience updated successfully"}
            else:
                return {"message": "Experience not found"}
        else:
            return {"message": "Candidat not found"}


# Delete user experience
@app.delete("/candidats/{candidat_id}/experience/{experience_id}")
async def delete_candidat_experience(candidat_id: int, experience_id: int):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            db_experience = await session.get(Experience, experience_id)
            if db_experience:
                await session.delete(db_experience)  # Await the coroutine
                await session.commit()
                return {"message": "Experience deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Experience not found")
        else:
            raise HTTPException(status_code=404, detail="Candidat not found")

#EDUCATION CRUD
# Create a new Education for a given User
@app.post("/candidats/{candidat_id}/education")
async def create_candidat_education(candidat_id: int, education: CreateEducationRequest):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            db_education = Education(
                candidat_id=candidat_id,
                institut=education.institut,
                start_at=education.start_at,
                end_at=education.end_at,
                diploma=education.diploma
            )
            session.add(db_education)
            await session.commit()
            return {"message": "Education created successfully"}
        else:
            return {"message": "Candidat not found"}

# Retrieve all Education records for a given User
@app.get("/candidats/{candidat_id}/education")
async def get_candidat_education(candidat_id: int):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            educations = await session.execute(select(Education).where(Education.candidat_id == candidat_id))
            candidat_educations = [dict(education._asdict()) for education in educations]
            return {"educations": candidat_educations}
        else:
            return {"message": "Candidat not found"}

# Update candidat education
@app.put("/candidats/{candidat_id}/education/{education_id}")
async def update_candidat_education(candidat_id: int, education_id: int, education: CreateEducationRequest):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            db_education = await session.get(Education, education_id)
            if db_education:
                db_education.institut = education.institut
                db_education.start_at = education.start_at
                db_education.end_at = education.end_at
                db_education.diploma = education.diploma
                await session.commit()
                return {"message": "Education updated successfully"}
            else:
                return {"message": "Education not found"}
        else:
            return {"message": "Candidat not found"}

# Delete candidat education
@app.delete("/candidats/{candidat_id}/education/{education_id}")
async def delete_candidat_education(candidat_id: int, education_id: int):
    async with async_session() as session: # type: ignore
        candidat = await session.get(Candidat, candidat_id)
        if candidat:
            db_education = await session.get(Education, education_id)
            if db_education:
                await session.delete(db_education)
                await session.commit()
                return {"message": "Education deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Education not found")
        else:
            raise HTTPException(status_code=404, detail="Candidat not found")


#The API for Authentication with JWT #

# Define the get_session function to create a new session for each request
def get_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False) # type: ignore
    return async_session() # type: ignore
#Define the user registration and login routes
@app.post("/register")
async def register_user(user_request: UserRegisterRequest, session: AsyncSession = Depends(get_session)):
    # Check if the user already exists in the database
    user = await session.execute(select(User).where(User.username == user_request.username))
    if user.scalar():
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_password = pwd_context.hash(user_request.password)

    # Create a new User object
    new_user = User(username=user_request.username, password=hashed_password)

    # Add the new user to the database
    session.add(new_user)
    await session.commit()

    return {"message": "User registered successfully"}


# login users
@app.post("/login")
async def login_user(user_request: UserLoginRequest, session: AsyncSession = Depends(get_session)):
    # Retrieve the user from the database
    user = await session.execute(select(User).where(User.username == user_request.username))
    user = user.scalar()

    if not user or not pwd_context.verify(user_request.password, user.password): # type: ignore
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Generate a JWT token
    token = generate_token(user.username) # type: ignore

    return {"token": token} 


def generate_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

#protected routes only for valid users
@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        # Perform additional authorization checks if necessary

        return {"message": f"Hello, {username}! This is a protected route."}
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.exceptions.DecodeError, jwt.exceptions.InvalidSignatureError):
        raise HTTPException(status_code=401, detail="Invalid token")

#get users
@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    # Retrieve all users from the database
    users = await session.execute(select(User))
    user_list = users.scalars().all()

    return {"users": user_list}

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
async def update_user(user_id: int, user: UserRegisterRequest):
    async with async_session() as session: # type: ignore
        db_user = await session.get(User, user_id)
        if db_user:
            db_user.username = user.username
            db_user.password = user.password
            await session.commit()
            return {"message": "User updated successfully"}
        else:
            return {"message": "User not found"}