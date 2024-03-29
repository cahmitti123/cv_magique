from pydantic import BaseModel
from typing import Optional

class CreateCvRequest(BaseModel):
    nom: Optional[str] 
    prenom: Optional[str] 
    address: Optional[str] 
    email: Optional[str] 
    city: Optional[str] 
    country: Optional[str] 
    postalcode: Optional[str] 
    tele: Optional[str] 
    brief: Optional[str] 
    img_url: Optional[str] 
    img_blob: Optional[str] 
    style: Optional[str] 
    color:Optional[str] 
    description:Optional[str] 
    experiences: Optional[str]                                              
    education: Optional[str] 
    languages: Optional[str] 
    skills: Optional[str] 
    loisirs: Optional[str] 
    is_experiences : Optional[bool]
    is_education : Optional[bool]
    is_languages : Optional[bool]
    is_skills : Optional[bool]
    is_loisirs : Optional[bool]
    is_active: Optional[bool]
    text_size: Optional[float]
    category_size: Optional[float]
    description_size:Optional[float]
    right_cate:Optional[str] 
    right_cate:Optional[str] 
    permis :Optional[str] 
    formatting :Optional[str] 
    left_cate:Optional[str] 
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
    img_blob:str
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
    text_size: float
    category_size: float
    description_size:float
    right_cate: str
    permis :str
    formatting :str
    left_cate: str
    
    

class UpdateCvRequest(BaseModel):
    nom: Optional[str] 
    prenom: Optional[str] 
    address: Optional[str] 
    email: Optional[str] 
    city: Optional[str] 
    country: Optional[str] 
    postalcode: Optional[str] 
    tele: Optional[str] 
    brief: Optional[str] 
    img_url: Optional[str] 
    img_blob: Optional[str] 
    style: Optional[str] 
    color:Optional[str] 
    description:Optional[str] 
    experiences: Optional[str]                                              
    education: Optional[str] 
    languages: Optional[str] 
    skills: Optional[str] 
    loisirs: Optional[str] 
    is_experiences : Optional[bool]
    is_education : Optional[bool]
    is_languages : Optional[bool]
    is_skills : Optional[bool]
    is_loisirs : Optional[bool]
    is_active: Optional[bool]
    text_size: Optional[float]
    category_size: Optional[float]
    description_size:Optional[float]
    right_cate:Optional[str] 
    permis :Optional[str] 
    formatting :Optional[str] 
    left_cate:Optional[str] 

     
    



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
    hashed_password: str = None

class UpdateCurrentUser(BaseModel):
    fullname: str = None
    is_active:bool = None
    hashed_password: str = None

class UserResponse(BaseModel):
    fullname: str
    email: str
    avatar: str
    is_admin:bool
    is_active:bool
    is_tutorial:bool

class UserLoginRequest(BaseModel):
    email: str
    hashed_password: str

class UpdatePasswordRequest(BaseModel):
    fullname:str
    current_password: str
    new_password: str

class CreateLetterRequest(BaseModel):
    a_prenom: Optional[str] 
    a_nom: Optional[str] 
    a_email: Optional[str] 
    a_ville: Optional[str] 
    a_adresse: Optional[str] 
    a_Code_postal: Optional[str] 
    a_tele: Optional[str] 
    b_prenom: Optional[str] 
    b_nom: Optional[str] 
    b_entreprise: Optional[str] 
    b_ville: Optional[str] 
    b_adresse: Optional[str] 
    b_Code_postal: Optional[str] 
    objet: Optional[str] 
    date: Optional[str] 
    lieu: Optional[str] 
    style:Optional[str] 
    signature_alignement:Optional[str]
    signature_couleur:Optional[str]
    signature_taille:Optional[str]
    signature_police:Optional[str]
    color:Optional[str] 
    lettre_de_motivation: Optional[str] 
    signature: Optional[str] 
    formatting :Optional[str] 
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
    style:str = None
    signature_alignement:str = None
    signature_couleur:str = None
    signature_taille:str = None
    signature_police:str = None
    color:str = None
    lettre_de_motivation: str = None
    signature: str = None
    formatting :str = None
    is_active:bool


#Create Public Cv

class CreatePublicCvRequest(BaseModel):
    nom: Optional[str] 
    prenom: Optional[str] 
    address: Optional[str] 
    email: Optional[str] 
    city: Optional[str] 
    country: Optional[str] 
    postalcode: Optional[str] 
    tele: Optional[str] 
    brief: Optional[str] 
    img_url: Optional[str] 
    img_blob: Optional[str] 
    style: Optional[str] 
    color:Optional[str] 
    description:Optional[str] 
    experiences: Optional[str]                                              
    education: Optional[str] 
    languages: Optional[str] 
    skills: Optional[str] 
    loisirs: Optional[str] 
    is_experiences : Optional[bool]
    is_education : Optional[bool]
    is_languages : Optional[bool]
    is_skills : Optional[bool]
    is_loisirs : Optional[bool]
    is_active: Optional[bool]
    text_size: Optional[float]
    category_size: Optional[float]
    description_size:Optional[float]
    right_cate:Optional[str] 
    permis :Optional[str] 
    formatting :Optional[str] 
    left_cate:Optional[str] 
    class Config:
        orm_mode = True

class CvPublicResponse(BaseModel):
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
    img_blob:str
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
    text_size: float
    category_size: float
    description_size:float
    right_cate: str
    permis :str
    formatting :str
    left_cate: str
    
    

class UpdatePublicCvRequest(BaseModel):
    nom: Optional[str] 
    prenom: Optional[str] 
    address: Optional[str] 
    email: Optional[str] 
    city: Optional[str] 
    country: Optional[str] 
    postalcode: Optional[str] 
    tele: Optional[str] 
    brief: Optional[str] 
    img_url: Optional[str] 
    img_blob: Optional[str] 
    style: Optional[str] 
    color:Optional[str] 
    description:Optional[str] 
    experiences: Optional[str]                                              
    education: Optional[str] 
    languages: Optional[str] 
    skills: Optional[str] 
    loisirs: Optional[str] 
    is_experiences : Optional[bool]
    is_education : Optional[bool]
    is_languages : Optional[bool]
    is_skills : Optional[bool]
    is_loisirs : Optional[bool]
    is_active: Optional[bool]
    text_size: Optional[float]
    category_size: Optional[float]
    description_size:Optional[float]
    right_cate:Optional[str] 
    permis :Optional[str] 
    formatting :Optional[str] 
    left_cate:Optional[str] 




#create public letter
class CreatePublicLetterRequest(BaseModel):
    a_prenom: Optional[str] 
    a_nom: Optional[str] 
    a_email: Optional[str] 
    a_ville: Optional[str] 
    a_adresse: Optional[str] 
    a_Code_postal: Optional[str] 
    a_tele: Optional[str] 
    b_prenom: Optional[str] 
    b_nom: Optional[str] 
    b_entreprise: Optional[str] 
    b_ville: Optional[str] 
    b_adresse: Optional[str] 
    b_Code_postal: Optional[str] 
    objet: Optional[str] 
    date: Optional[str] 
    lieu: Optional[str] 
    style:Optional[str]
    signature_alignement:Optional[str]
    signature_couleur:Optional[str]
    signature_taille:Optional[str]
    signature_police:Optional[str]
    color:Optional[str] 
    lettre_de_motivation: Optional[str] 
    signature: Optional[str] 
    formatting :Optional[str] 
    is_active: bool
    class Config:
        orm_mode = True

class UpdatePublicLetterRequest(BaseModel):
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
    style:str = None
    signature_alignement:str = None
    signature_couleur:str = None
    signature_taille:str = None
    signature_police:str = None
    color:str = None
    lettre_de_motivation: str = None
    signature: str = None
    formatting :str = None
    is_active:bool 


class CreateDeletedCvRequest(BaseModel):
    nom: Optional[str] 
    prenom: Optional[str] 
    address: Optional[str] 
    email: Optional[str] 
    city: Optional[str] 
    country: Optional[str] 
    postalcode: Optional[str] 
    tele: Optional[str] 
    brief: Optional[str] 
    img_url: Optional[str] 
    img_blob: Optional[str] 
    style: Optional[str] 
    color:Optional[str] 
    description:Optional[str] 
    experiences: Optional[str]                                              
    education: Optional[str] 
    languages: Optional[str] 
    skills: Optional[str] 
    loisirs: Optional[str] 
    is_experiences : Optional[bool]
    is_education : Optional[bool]
    is_languages : Optional[bool]
    is_skills : Optional[bool]
    is_loisirs : Optional[bool]
    is_active: Optional[bool]
    text_size: Optional[float]
    category_size: Optional[float]
    description_size:Optional[float]
    right_cate:Optional[str] 
    permis :Optional[str] 
    formatting :Optional[str] 
    left_cate:Optional[str] 
    class Config:
        orm_mode = True



class CreateDeletedLetterRequest(BaseModel):
    a_prenom: Optional[str] 
    a_nom: Optional[str] 
    a_email: Optional[str] 
    a_ville: Optional[str] 
    a_adresse: Optional[str] 
    a_Code_postal: Optional[str] 
    a_tele: Optional[str] 
    b_prenom: Optional[str] 
    b_nom: Optional[str] 
    b_entreprise: Optional[str] 
    b_ville: Optional[str] 
    b_adresse: Optional[str] 
    b_Code_postal: Optional[str] 
    objet: Optional[str] 
    date: Optional[str] 
    lieu: Optional[str] 
    style:Optional[str]
    signature_alignement:Optional[str]
    signature_couleur:Optional[str]
    signature_taille:Optional[str]
    signature_police:Optional[str]
    color:Optional[str] 
    lettre_de_motivation: Optional[str] 
    signature: Optional[str] 
    formatting :Optional[str] 
    is_active: bool
    class Config:
        orm_mode = True










