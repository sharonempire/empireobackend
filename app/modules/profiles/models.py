from sqlalchemy import BigInteger, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    diplay_name = Column(Text, nullable=True)  # Note: typo in DB (diplay not display)
    profilepicture = Column(Text, nullable=True)
    user_type = Column(Text, nullable=True)
    phone = Column(BigInteger, nullable=True)
    designation = Column(Text, nullable=True)
    freelancer_status = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    callerId = Column(Text, nullable=True, unique=True)  # Unique caller ID
    countries = Column(ARRAY(Text), nullable=True)
    fcm_token = Column(Text, nullable=True)
    user_id = Column(Text, nullable=True)

