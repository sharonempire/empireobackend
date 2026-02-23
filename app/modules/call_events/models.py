from sqlalchemy import BigInteger, Column, DateTime, Integer, Text

from app.database import Base


class CallEvent(Base):
    __tablename__ = "call_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    event_type = Column(Text, nullable=False)
    call_uuid = Column(Text, nullable=True)
    caller_number = Column(Text, nullable=True)
    called_number = Column(Text, nullable=True)
    agent_number = Column(Text, nullable=True)
    call_status = Column(Text, nullable=True)
    total_duration = Column(Integer, nullable=True)
    conversation_duration = Column(Integer, nullable=True)
    call_start_time = Column(DateTime(timezone=True), nullable=True)
    call_end_time = Column(DateTime(timezone=True), nullable=True)
    recording_url = Column(Text, nullable=True)
    dtmf = Column(Text, nullable=True)
    transferred_number = Column(Text, nullable=True)
    destination = Column(Text, nullable=True)
    callerid = Column(Text, nullable=True)
    call_date = Column(Text, nullable=True)
    extension = Column(Text, nullable=True)
    caller_phone_norm = Column(Text, nullable=True)
    agent_phone_norm = Column(Text, nullable=True)
