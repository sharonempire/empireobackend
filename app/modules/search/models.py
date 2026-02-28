from sqlalchemy import BigInteger, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.database import Base


class DomainKeywordMap(Base):
    __tablename__ = "domain_keyword_map"

    domain = Column(Text, primary_key=True)
    keywords = Column(ARRAY(Text), nullable=True)


class SearchSynonym(Base):
    __tablename__ = "search_synonyms"

    trigger = Column(Text, primary_key=True)
    expansion = Column(Text, nullable=True)


class Stopword(Base):
    __tablename__ = "stopwords"

    word = Column(Text, primary_key=True)


class BacklogParticipant(Base):
    __tablename__ = "backlog_participants"

    day = Column(Text, primary_key=True)
    employee_id = Column(UUID(as_uuid=True), primary_key=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    email = Column(Text, nullable=True)
    full_name = Column(Text, nullable=True)
    main_location = Column(Text, nullable=True)
    full_location = Column(Text, nullable=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True)
