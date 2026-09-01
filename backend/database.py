import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Text, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_DB_PATH = os.path.join(DATA_DIR, "recoverai.db")
DB_PATH = os.environ.get("DATABASE_PATH") or DEFAULT_DB_PATH
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()


class LivePaymentModel(Base):
    __tablename__ = "live_payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="created")
    payment_method = Column(String(50), default="Card")
    bank = Column(String(100), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_description = Column(Text, nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIIntelligenceResultModel(Base):
    __tablename__ = "ai_intelligence_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), index=True, nullable=False)
    recovery_probability = Column(Float, nullable=True)
    prediction_band = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    prediction_mode = Column(String(100), nullable=True)
    feature_completeness = Column(Float, nullable=True)
    root_cause = Column(Text, nullable=True)
    root_cause_confidence = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=True)
    recommendation_score = Column(Float, nullable=True)
    expected_recovery_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RecoveryActionModel(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    action_type = Column(String(50), nullable=False)
    incident_id = Column(String(100), nullable=True)
    execution_mode = Column(String(50), default="TEST_SIMULATION")
    recovery_state = Column(String(50), default="AWAITING_RETRY")
    strategy_name = Column(String(100), nullable=True)
    next_step = Column(Text, nullable=True)
    status = Column(String(50), default="executed")
    execution_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class PaymentEventModel(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    event_description = Column(Text, nullable=False)
    metadata_json = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookEventModel(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    payment_id = Column(String(100), nullable=True)
    event_type = Column(String(100), nullable=False)
    processed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InfrastructureIncidentModel(Base):
    __tablename__ = "infrastructure_incidents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String(100), unique=True, index=True, nullable=False)
    payment_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    gateway = Column(String(100), nullable=False)
    payment_method = Column(String(50), nullable=False)
    error_code = Column(String(100), nullable=True)
    error_reason = Column(String(100), nullable=True)
    title = Column(String(200), nullable=False)
    severity = Column(String(20), default="WARNING")
    confidence = Column(Float, default=0.90)
    root_cause = Column(Text, nullable=True)
    amount_at_risk = Column(Float, default=0.0)
    recommended_mitigation = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")
    source = Column(String(50), default="razorpay_test_webhook")
    affected_transactions_count = Column(Integer, default=1)
    grouping_key = Column(String(150), index=True, nullable=True)
    affected_payment_ids = Column(Text, nullable=True)
    impacted_merchants_count = Column(Integer, default=1)
    mitigated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initializes SQLite database tables automatically and applies schema migrations."""
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            # Infrastructure Incidents migrations
            res_inc = conn.execute(text("PRAGMA table_info(infrastructure_incidents)")).fetchall()
            cols_inc = [row[1] for row in res_inc] if res_inc else []
            if "grouping_key" not in cols_inc:
                conn.execute(text("ALTER TABLE infrastructure_incidents ADD COLUMN grouping_key VARCHAR(150)"))
            if "affected_payment_ids" not in cols_inc:
                conn.execute(text("ALTER TABLE infrastructure_incidents ADD COLUMN affected_payment_ids TEXT"))
            if "impacted_merchants_count" not in cols_inc:
                conn.execute(text("ALTER TABLE infrastructure_incidents ADD COLUMN impacted_merchants_count INTEGER DEFAULT 1"))

            # Recovery Actions migrations
            res_act = conn.execute(text("PRAGMA table_info(recovery_actions)")).fetchall()
            cols_act = [row[1] for row in res_act] if res_act else []
            if "incident_id" not in cols_act:
                conn.execute(text("ALTER TABLE recovery_actions ADD COLUMN incident_id VARCHAR(100)"))
            if "execution_mode" not in cols_act:
                conn.execute(text("ALTER TABLE recovery_actions ADD COLUMN execution_mode VARCHAR(50) DEFAULT 'TEST_SIMULATION'"))
            if "recovery_state" not in cols_act:
                conn.execute(text("ALTER TABLE recovery_actions ADD COLUMN recovery_state VARCHAR(50) DEFAULT 'AWAITING_RETRY'"))
            if "strategy_name" not in cols_act:
                conn.execute(text("ALTER TABLE recovery_actions ADD COLUMN strategy_name VARCHAR(100)"))
            if "next_step" not in cols_act:
                conn.execute(text("ALTER TABLE recovery_actions ADD COLUMN next_step TEXT"))

            conn.commit()
    except Exception as e:
        print(f"[init_db] Column migration notice: {e}")


def get_db():
    """Dependency or helper to retrieve a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
