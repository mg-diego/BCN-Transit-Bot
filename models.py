from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Boolean, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from providers.database.database import Base 

# ----------------------------
# USUARIOS
# ----------------------------
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)

    username = Column(String, nullable=True)
    language = Column(String, default="es")
    created_at = Column(DateTime, server_default=func.now())
    
    receive_notifications = Column(Boolean, default=True)
    already_notified_ids = Column(JSONB, default=list) 

    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    audit_trail = relationship("AuditLog", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")

class UserDevice(Base):
    __tablename__ = "user_devices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False)
    user = relationship("User", back_populates="devices")

# ----------------------------
# FAVORITOS
# ----------------------------
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    transport_type = Column(String, nullable=False)
    station_code = Column(String, nullable=False)
    station_name = Column(String, nullable=False)
    station_group_code = Column(String, nullable=True)
    
    line_name = Column(String, nullable=True)
    line_name_with_emoji = Column(String, nullable=True)
    line_code = Column(String, nullable=True)    

    latitude = Column(Float, nullable=True) 
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="favorites")

# ----------------------------
# DATOS DE SERVICIO (TMB/RODALIES)
# ----------------------------
class ServiceIncident(Base):
    """
    Guarda los datos de tu tabla 'ALERTS' (los avisos globales del servicio).
    Usamos JSONB para guardar 'PUBLICATIONS' y 'AFFECTED_ENTITIES' tal cual vienen.
    """
    __tablename__ = "service_incidents"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True)
    
    transport_type = Column(String)
    begin_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    
    status = Column(String)
    cause = Column(String)
    
    publications = Column(JSONB) 
    affected_entities = Column(JSONB)

# ----------------------------
# SUSCRIPCIONES DE USUARIO
# ----------------------------
class UserSubscription(Base):
    """
    Lo que antes llamábamos 'Alert'. Configuración del usuario.
    """
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    line_id = Column(String)
    days_active = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    
    user = relationship("User", back_populates="subscriptions")

# ----------------------------
# AUDIT & HISTORY
# ----------------------------
class AuditLog(Base):
    __tablename__ = "audit_trail"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_source = Column(String, index=True, nullable=False)
    
    action = Column(String)
    details = Column(JSONB)
    
    user = relationship("User", back_populates="audit_trail")
    __table_args__ = (
        Index('ix_audit_details', details, postgresql_using='gin'),
    )

class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String)
    timestamp = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="search_history")