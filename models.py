from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Candidat(Base):
    __tablename__ = "candidats"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(50))
    prenom = Column(String(50))
    address = Column(String(50))
    email = Column(String(50))
    city = Column(String(256))
    country = Column(String(256))
    postalcode = Column(String(256))
    tele = Column(String(256))
    skills = Column(String(256))
    img_url = Column(String(256))
    education = relationship("Education", back_populates="candidat", cascade="all, delete")
    experience = relationship("Experience", back_populates="candidat", cascade="all, delete")


class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, index=True)
    candidat_id = Column(Integer, ForeignKey("candidats.id"))
    societe = Column(String(50))
    start_at = Column(String(50))
    end_at = Column(String(10))
    job = Column(String(10))
    candidat = relationship("Candidat", back_populates="experience")


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    candidat_id = Column(Integer, ForeignKey("candidats.id"))
    institut = Column(String(50))
    start_at = Column(String(50))
    end_at = Column(String(10))
    diploma = Column(String(10))
    candidat = relationship("Candidat", back_populates="education")



class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100))
    