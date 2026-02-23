from sqlalchemy import BigInteger, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY

from app.database import Base


class DomainKeywordMap(Base):
    __tablename__ = "domain_keyword_map"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    domain = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class SearchSynonym(Base):
    __tablename__ = "search_synonyms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    term = Column(Text, nullable=True)
    synonyms = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class Stopword(Base):
    __tablename__ = "stopwords"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    word = Column(Text, nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class BacklogParticipant(Base):
    __tablename__ = "backlog_participants"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    participant_id = Column(Text, nullable=True)
    backlog_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class UserProfile(Base):
    """Legacy user_profiles table if it exists."""
    __tablename__ = "user_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    profile_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

