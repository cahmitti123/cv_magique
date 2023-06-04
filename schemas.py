from pydantic import BaseModel

class CreateCvRequest(BaseModel):
    nom: str
    prenom: str
    address: str
    email: str
    city: str
    country: str
    postalcode: str
    tele: str
    brief: str
    img_url: str
    style:str
    color:str
    description:str
    experiences: str
    education: str
    languages: str
    skills: str 
    loisirs: str
    class Config:
        orm_mode = True

class CvResponse(BaseModel):
    id: str
    nom: str
    prenom: str
    address: str
    email: str
    city: str
    country: str
    postalcode: str
    tele: str
    brief: str
    img_url: str
    style:str
    color:str
    description:str
    experiences: str
    education: str
    languages: str
    skills: str 
    loisirs:str
    

class UpdateCvRequest(BaseModel):
    nom: str = None
    prenom: str = None
    address: str = None
    email: str = None
    city: str = None
    country: str = None
    postalcode: str = None
    tele: str = None
    brief: str = None
    img_url: str = None
    style:str = None
    color:str = None
    description:str = None
    experiences: str = None
    education: str = None
    languages: str = None
    skills: str = None
    loisirs:str = None
    



class CreateUserRequest(BaseModel):
    fullname: str
    email: str
    avatar: str
    hashed_password: str

class UpdateUserRequest(BaseModel):
    fullname: str = None
    email: str = None
    avatar: str = None
    is_admin: bool = None
    is_active:bool = None

class UserResponse(BaseModel):
    fullname: str
    email: str
    avatar: str
    is_admin:bool
    is_active:bool

class UserLoginRequest(BaseModel):
    email: str
    hashed_password: str
