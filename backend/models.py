from sqlalchemy import Column, DateTime, Integer, Float, String, Text
from datetime import datetime
from database import Base

class IncidentModel(Base):
    __tablename__ = "incidentmodels"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    animal_type = Column(String, nullable=False)
    injury_description = Column(String, nullable=False)
    created_at = Column(DateTime, default = datetime.utcnow, nullable=False)
    # Add this field to store the scraped results in the database
    source = Column(Text, nullable=True)
    scraped_clinics = Column(Text, nullable=True)

    