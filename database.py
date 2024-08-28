from xmlrpc.client import Boolean

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
database_path = 'postgresql+psycopg2://postgres:12385279@89.23.97.213:5432/w4udatabase'
from sqlalchemy import create_engine, Float, BigInteger
from sqlalchemy import create_engine, MetaData, Table, Integer, String, Enum,Column, DateTime, ForeignKey, Numeric

from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped
from datetime import datetime, timedelta


engine = create_engine(database_path, pool_pre_ping=True)
engine.connect()
Session = sessionmaker(engine)
Session.configure(bind=engine)



naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base:
    __allow_unmapped__ = True


metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata, cls=Base)

class User(Base):
    __tablename__='users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String,unique=True)
    real_name = Column(String)
    age = Column(Integer)
    gender = Column(Enum('men', 'women', name='gender'))
    created_at:datetime = Column(DateTime)


class Marker(Base):
    __tablename__ = 'marker'
    id = Column(Integer, primary_key=True)
    user = Column(Integer , ForeignKey('users.id'))
    latitude = Column(Float)
    longitude = Column(Float)
    type = Column(Enum('red', 'blue', name='type'))
    created_at: datetime = Column(DateTime)

class MarkerHistory(Base):
    __tablename__ = 'markerhistory'
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('users.id'))
    marker = Column(Integer,ForeignKey('marker.id'))
    match = Column(Integer,ForeignKey('match.id'))
    latitude = Column(Float)
    longitude = Column(Float)
    requested_at = Column(DateTime)

class Match(Base):
    __tablename__ = 'match'
    id = Column(Integer, primary_key=True)
    user_1 = Column(Integer, ForeignKey('users.id'))
    user_2 = Column(Integer,ForeignKey('users.id'))
    created_at: datetime = Column(DateTime)

class Message(Base):
    __tablename__ = 'messsage'
    id = Column(Integer, primary_key=True)
    match = Column(Integer,ForeignKey('match.id'))
    sender = Column(Integer,ForeignKey('users.id'))
    content = Column(String)
    timestamp = Column(DateTime)
    read = Column(Integer, default=0)