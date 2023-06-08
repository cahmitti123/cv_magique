from pydantic import BaseModel,Field

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
    is_active: bool = Field(None,description='optionl')
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
    is_active : bool
    
    

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
    is_active: bool = Field(None,description='optionl')
    



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


class CreateLetterRequest(BaseModel):
    a_prenom: str
    a_nom: str
    a_email: str
    a_ville: str
    a_adresse: str
    a_Code_postal: str
    a_tele: str
    b_prenom: str
    b_nom: str
    b_entreprise: str
    b_ville: str
    b_adresse: str
    b_Code_postal: str
    objet: str
    date: str
    lieu: str
    lettre_de_motivation: str
    signature: str
    is_active: bool
    class Config:
        orm_mode = True

class UpdateLetterRequest(BaseModel):
    a_prenom: str = None
    a_nom: str = None
    a_email: str = None
    a_ville: str = None
    a_adresse: str = None
    a_Code_postal: str = None
    a_tele: str = None
    b_prenom: str = None
    b_nom: str = None
    b_entreprise: str = None
    b_ville: str = None
    b_adresse: str = None
    b_Code_postal: str = None
    objet: str = None
    date: str = None
    lieu: str = None
    lettre_de_motivation: str = None
    signature: str = None
    is_active:bool