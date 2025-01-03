from sqlalchemy import Column, String, Float, Integer, Boolean, Text 
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProductTable(Base):
    __tablename__ = 'products'
    link = Column(String, primary_key=True, nullable=False, unique=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    characteristics = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    views = Column(Integer, nullable=True)
    date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    seller_id = Column(String, foreign_key=True, nullable=False)
    today_views = Column(Integer, nullable=True)
    about = Column(Text, nullable=True)
    is_sold = Column(Boolean, nullable=False)

class SellerTable(Base):
    __tablename__ = 'sellers'
    seller_id = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    rating = Column(Float, nullable=True)
    reviews = Column(Integer, nullable=True)
    subscribers = Column(Integer, nullable=True)
    subscriptions = Column(Integer, nullable=True)
    registered = Column(String, nullable=True)
    done_deals = Column(Integer, nullable=True)
    active_deals = Column(Integer, nullable=True)
    docs_confirmed = Column(Boolean, nullable=True)
    phone_confirmed = Column(Boolean, nullable=True)
    response_time = Column(String, nullable=True)
