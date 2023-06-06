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
    is_experiences : bool
    is_education : bool
    is_languages : bool
    is_skills : bool
    is_loisirs : bool
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
    is_experiences : bool
    is_education : bool
    is_languages : bool
    is_skills : bool
    is_loisirs : bool
    
    

class UpdateCvRequest(BaseModel):
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
    is_experiences : bool
    is_education : bool
    is_languages : bool
    is_skills : bool
    is_loisirs : bool
    



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
