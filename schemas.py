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
    experiences: str
    education: str
    languages: str
    user_id: int
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
    experiences: str
    education: str
    languages: str
    user_id: int

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
    experiences: str = None
    education: str = None
    languages: str = None
    user_id: int = None



class CreateUserRequest(BaseModel):
    fullname: str
    email: str
    avatar: str
    hashed_password: str
    is_admin: bool

class UpdateUserRequest(BaseModel):
    fullname: str = None
    email: str = None
    avatar: str = None
    hashed_password: str = None
    is_admin: bool = None

class UserResponse(BaseModel):
    fullname: str
    email: str
    avatar: str

class UserLoginRequest(BaseModel):
    email: str
    hashed_password: str
