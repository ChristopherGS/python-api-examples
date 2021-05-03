import uuid

from app.database import Base

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = Column(String(256), index=True)
    email = Column(String, index=True, nullable=False)

    # Dates are always in UTC. If null then email not validated.
    email_validated_date = Column(DateTime)

    hashed_password = Column(String, nullable=False)