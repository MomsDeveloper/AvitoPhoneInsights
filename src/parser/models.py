from pydantic import BaseModel, Field, field_validator
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
