from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from database import Base


class PolicyORM(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True)
    policy_group_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    natural_language = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RuleORM(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    condition_type = Column(String, nullable=False)
    condition_value = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
