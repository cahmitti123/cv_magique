from pydantic import BaseModel

class CreateCandidatRequest(BaseModel):
    nom: str
    prenom: str
    address: str
    email: str
    city: str
    country: str
    postalcode: str
    tele: str
    skills: str
    img_url: str

class CreateExperienceRequest(BaseModel):
    societe: str
    start_at: str
    end_at: str
    job: str

class CreateEducationRequest(BaseModel):
    institut: str
    start_at: str
    end_at: str
    diploma: str



class UserRegisterRequest(BaseModel):
    username: str
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str