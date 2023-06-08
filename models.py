from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Cv(Base):
    __tablename__ = "cvs"
    id = Column(String(50), primary_key=True, index=True)
    nom = Column(String(50))
    prenom = Column(String(50))
    address = Column(String(50))
    email = Column(String(50))
    city = Column(String(256))
    country = Column(String(256))
    postalcode = Column(String(256))
    tele = Column(String(256))
    brief = Column(String(50))
    img_url = Column(String(256))
    style = Column(String(256))
    color = Column(String(256))
    description = Column(String(256))
    experiences = Column(Text(600))
    education = Column(Text(600))
    languages = Column(Text(600))
    skills = Column(Text(600))
    loisirs = Column(Text(600))
    is_experiences = Column(Boolean, default=True) 
    is_education = Column(Boolean, default=True) 
    is_languages = Column(Boolean, default=True)
    is_skills = Column(Boolean, default=True)
    is_loisirs = Column(Boolean, default=True)
    is_active = Column(Boolean,default=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship("User", back_populates="cvs")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100))
    email = Column(String(50), unique=True, index=True)
    avatar = Column(String(100))
    hashed_password = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    cvs = relationship("Cv", back_populates="user", cascade="all, delete")
    letters = relationship("Letter", back_populates="user", cascade="all, delete")




class Letter(Base):
    __tablename__ = "letters"
    id = Column(String(50), primary_key=True, index=True)
    a_prenom= Column(String(256))
    a_nom= Column(String(256))
    a_email= Column(String(256))
    a_ville= Column(String(256))
    a_adresse= Column(String(256))
    a_Code_postal= Column(String(256))
    a_tele= Column(String(256))
    b_prenom= Column(String(256))
    b_nom= Column(String(256))
    b_entreprise= Column(String(256))
    b_ville= Column(String(256))
    b_adresse= Column(String(256))
    b_Code_postal= Column(String(256))
    objet= Column(String(256))
    date= Column(String(256))
    lieu= Column(String(256))
    lettre_de_motivation= Column(Text(600))
    signature= Column(String(256))
    is_active= Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship("User", back_populates="letters")
