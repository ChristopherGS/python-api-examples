import uuid

from app.database import Base, engine

from sqlalchemy import Column, DateTime, String, Integer, Boolean


class User(Base):
    __tablename__ = 'User'

    id = Column(
        Integer,
        primary_key=True,
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = Column(String(256), index=True)
    username = Column(String(256))
    email = Column(String, index=True, nullable=False)

    # Dates are always in UTC. If null then email not validated.
    email_validated_date = Column(DateTime)

    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)

Base.metadata.create_all(engine)