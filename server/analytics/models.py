from pydantic import BaseModel, field_validator
from typing import Optional
import re
import json

class Product(BaseModel):
    link: str
    title: str
    price: float
    characteristics: Optional[str]
    description: Optional[str]
    views: Optional[int]
    date: Optional[str]
    location: Optional[str]
    seller_id: str
    today_views: Optional[int]
    about: Optional[str]
    is_sold: bool
    version: Optional[int]
    is_pro: bool
    is_max: bool
    capacity: Optional[int]
    condition: Optional[str]

    @field_validator('price', mode='before')
    def parse_price(cls, value):
        # Convert price to a float if it's a string
        return float(re.sub(r'[^\d.]', '', value)) if isinstance(value, str) else value

    @field_validator('views', 'today_views', mode='before')
    def parse_views(cls, value):
        # Convert views to an integer if it's a string
        return int(re.sub(r'\D', '', value)) if isinstance(value, str) else value
    
    @field_validator('characteristics', 'about', mode='before')
    def dict_to_json(cls, value):
        return json.dumps(value) if isinstance(value, dict) else value
    
    @field_validator('date', mode='before')
    #   Input should be a valid string [type=string_type, input_value=Timestamp('2024-03-26 11:35:00'), input_type=Timestamp]
    def parse_date(cls, value):
        # Convert date to a string if it's a Timestamp
        return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'strftime') else value

class Seller(BaseModel):
    seller_id: str
    name: str
    rating: Optional[float]
    reviews: Optional[int]
    subscribers: Optional[int]
    subscriptions: Optional[int]
    registered: Optional[str]
    done_deals: Optional[int]
    active_deals: Optional[int]
    docs_confirmed: Optional[bool]
    phone_confirmed: Optional[bool]
    response_time: Optional[str]

    @field_validator('registered', mode='before')
    def parse_registered(cls, value):
        # Convert registered to a string if it's a Timestamp
        return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'strftime') else value
