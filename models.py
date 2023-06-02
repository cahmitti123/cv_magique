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
    experiences = Column(Text(600))
    education = Column(Text(600))
    languages = Column(Text(600))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship("User", back_populates="cvs")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100))
    email = Column(String(50), unique=True, index=True)
    avatar = Column(String(100))
    hashed_password = Column(String(100))
    cvs = relationship("Cv", back_populates="user", cascade="all, delete")
    is_admin = Column(Boolean, default=False)





