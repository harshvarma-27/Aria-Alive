from sqlalchemy import Column, Integer, String, Text
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    age_group = Column(String, nullable=False)            # e.g., "Child", "Adult", "Senior"
    gender = Column(String, nullable=True)
    conditions = Column(Text, nullable=True)              # comma-separated conditions
    smoking = Column(String, nullable=True)               # "Yes"/"No"
    outdoor_time = Column(String, nullable=True)          # free text like "2 hours"
    location = Column(String, nullable=False)             # city name string
