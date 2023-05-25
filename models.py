from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()



class Candidat(Base):
    __tablename__ = "candidats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    nom = Column(String(50))
    prenom = Column(String(50))
    address = Column(String(50))
    email = Column(String(50))
    city = Column(String(256))
    country = Column(String(256))
    postalcode = Column(String(256))
    experience = Column(Text(600))
    education = Column(Text(600))
    tele = Column(String(256))
    skills = Column(String(256))
    img_url = Column(String(256))
    user = relationship("User", back_populates="candidats")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(50), unique=True, index=True)
    password = Column(String(100))
    is_admin = Column(Boolean, default=False)
    candidat = relationship("Candidat", back_populates="user", cascade="all, delete")


class Model(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)