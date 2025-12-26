import asyncio
import inspect
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from functools import wraps

# SQLAlchemy & DB
from sqlalchemy import select, delete, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from domain.clients import ClientType
from providers.database.database import AsyncSessionLocal
from models import (
    User as DBUser, 
    Favorite as DBFavorite, 
    ServiceIncident as DBServiceIncident, 
    AuditLog as DBAuditLog, 
    SearchHistory as DBSearchHistory,
    UserDevice as DBUserDevice
)

# Domain Models
from domain.api.favorite_model import FavoriteItem
from domain.common.alert import AffectedEntity, Alert, Publication
from domain.common.user import User
from domain.transport_type import TransportType

# Telegram
from telegram import Update

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# DECORADOR DE AUDITORÍA (Debe estar definido antes de la clase)
# -------------------------------------------------------------------------
def audit_action(action_type: str, params_args: list = None):
    """
    Decorador para métodos de UserDataManager.
    Extrae user_id y client_source directamente de los argumentos de la función.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # -------------------------------------------------------
            # 1. EJECUCIÓN INMEDIATA
            # -------------------------------------------------------
            try:
                result = await func(self, *args, **kwargs)
                status = "SUCCESS"
                error_info = None
            except Exception as e:
                result = e
                status = "ERROR"
                error_info = str(e)

            # -------------------------------------------------------
            # 2. EXTRACCIÓN DE DATOS (Usando Inspección de Firma)
            # -------------------------------------------------------
            try:
                # Esto "mapea" los args y kwargs a los nombres reales de los parámetros de la función
                sig = inspect.signature(func)
                # self ya está en el wrapper, bindeamos el resto
                bound_args = sig.bind(self, *args, **kwargs)
                bound_args.apply_defaults()
                
                # Diccionario con todos los valores pasados a la función
                func_args = bound_args.arguments

                # Extraemos datos clave
                # Convertimos a str para asegurar compatibilidad (Enum -> str, Int -> str)
                
                raw_source = func_args.get("client_source", "UNKNOWN")
                source = str(raw_source.value) if hasattr(raw_source, "value") else str(raw_source)

                raw_user_id = func_args.get("user_id")
                user_id_ext = str(raw_user_id) if raw_user_id is not None else None

                # Preparamos detalles
                details = {
                    "params": {},
                    "status": status
                }
                if error_info:
                    details["error"] = error_info

                # Extraemos parámetros adicionales solicitados en params_args
                if params_args:
                    for param_name in params_args:
                        if param_name in func_args:
                            val = func_args[param_name]
                            # Manejo inteligente de tipos (Enums, Pydantic, etc)
                            if hasattr(val, "value"): # Enum
                                val_str = str(val.value)
                            elif hasattr(val, "model_dump_json"): # Pydantic v2
                                val_str = val.model_dump_json()
                            elif hasattr(val, "dict"): # Pydantic v1
                                val_str = str(val.dict())
                            else:
                                val_str = str(val)
                            
                            details["params"][param_name] = val_str

                # -------------------------------------------------------
                # 3. GUARDADO ASÍNCRONO
                # -------------------------------------------------------
                # Como el decorador está EN el UserDataManager, 'self' ES el manager.
                if user_id_ext and hasattr(self, "save_audit_log_background"):
                    asyncio.create_task(
                        self.save_audit_log_background(
                            user_id_ext=user_id_ext,
                            source=source,
                            action=action_type,
                            details=details
                        )
                    )
                else:
                    if user_id_ext:
                        logger.error(f"[Audit] Method save_audit_log_background not found in {self.__class__.__name__}")

            except Exception as log_err:
                logger.error(f"[Audit] Failed to log action: {log_err}")

            # -------------------------------------------------------
            # 4. FINALIZACIÓN
            # -------------------------------------------------------
            if status == "ERROR" and isinstance(result, Exception):
                raise result

            return result
        return wrapper
    return decorator


# -------------------------------------------------------------------------
# CLASE USER DATA MANAGER
# -------------------------------------------------------------------------
class UserDataManager:
    """
    Gestor de datos usando PostgreSQL + SQLAlchemy (Async).
    Reemplaza al antiguo gestor basado en Google Sheets.
    """

    FAVORITE_TYPE_ORDER = {
        TransportType.METRO.value: 0,
        TransportType.BUS.value: 1,
        TransportType.TRAM.value: 2,
        TransportType.RODALIES.value: 3
    }

    def __init__(self):
        logger.info("Initializing UserDataManager with PostgreSQL...")

    async def save_audit_log_background(self, user_id_ext, source, action, details):
        """Tarea en segundo plano: no bloquea la respuesta al usuario"""
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(DBUser.id).where(DBUser.external_id == str(user_id_ext))
                res = await session.execute(stmt)
                internal_id = res.scalars().first()

                new_log = DBAuditLog(
                    user_id=internal_id,
                    client_source=source,
                    action=action,
                    details=details
                )
                session.add(new_log)
                await session.commit()
            except Exception as e:
                logger.error(f"[Audit] DB Write Failed: {e}")


    async def _get_user_internal_id(self, session: AsyncSession, external_id: str) -> Optional[int]:
        """Busca el ID numérico (PK) a partir del ID de Telegram/Android"""
        stmt = select(DBUser.id).where(DBUser.external_id == str(external_id))
        result = await session.execute(stmt)
        return result.scalars().first()

    # ---------------------------
    # USERS
    # ---------------------------

    @audit_action(action_type="REGISTER_USER", params_args=["username"])
    async def register_user(self, client_source: ClientType, user_id: str, username: str, fcm_token: str = "") -> bool:
        """Registra usuario o actualiza su token/última actividad."""
        async with AsyncSessionLocal() as session:
            try:
                # Buscar usuario
                stmt = select(DBUser).where(DBUser.external_id == str(user_id))
                result = await session.execute(stmt)
                db_user = result.scalars().first()
                
                is_new = False

                if not db_user:
                    # Crear nuevo
                    is_new = True
                    db_user = DBUser(
                        external_id=str(user_id),
                        username=username,
                        language="es", # Default
                        receive_notifications=True
                    )
                    session.add(db_user)
                    await session.flush() # Para obtener el ID generado
                else:
                    if username:
                        db_user.username = username

                # Gestionar Dispositivo (FCM)
                if fcm_token:
                    stmt_device = select(DBUserDevice).where(
                        and_(DBUserDevice.user_id == db_user.id, DBUserDevice.token == fcm_token)
                    )
                    res_device = await session.execute(stmt_device)
                    device = res_device.scalars().first()

                    if not device:
                        new_device = DBUserDevice(user_id=db_user.id, token=fcm_token)
                        session.add(new_device)

                await session.commit()
                return is_new
            except Exception as e:
                logger.error(f"Error registering user {user_id}: {e}")
                await session.rollback()
                return False

    @audit_action(action_type="UPDATE_LANGUAGE", params_args=["new_language"])
    async def update_user_language(self, client_source: ClientType, user_id: int, new_language: str):
        async with AsyncSessionLocal() as session:
            stmt = update(DBUser).where(DBUser.external_id == str(user_id)).values(language=new_language)
            await session.execute(stmt)
            await session.commit()
            return True

    async def get_user_language(self, user_id: int) -> str:
        async with AsyncSessionLocal() as session:
            stmt = select(DBUser.language).where(DBUser.external_id == str(user_id))
            result = await session.execute(stmt)
            lang = result.scalars().first()
            return lang if lang else "en"

    @audit_action(action_type="GET_ALL_USERS", params_args=[])
    async def get_users(self, client_source: ClientType = ClientType.SYSTEM.value) -> List[User]:
        async with AsyncSessionLocal() as session:
            stmt = select(DBUser)
            result = await session.execute(stmt)
            db_users = result.scalars().all()
            
            return [
                User(
                    user_id=u.external_id,
                    username=u.username,
                    created_at=u.created_at,
                    language=u.language,
                    receive_notifications=u.receive_notifications,
                    already_notified=u.already_notified_ids if u.already_notified_ids else [], 
                    fcm_token=""
                ) for u in db_users
            ]

    @audit_action(action_type="UPDATE_NOTIFIED_ALERTS", params_args=["alert_id"])
    async def update_notified_alerts(self, user_id, alert_id, client_source: ClientType = ClientType.SYSTEM.value):
        async with AsyncSessionLocal() as session:
            stmt = select(DBUser).where(DBUser.external_id == str(user_id))
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user:
                current_list = list(user.already_notified_ids) if user.already_notified_ids else []
                if alert_id not in current_list:
                    current_list.append(alert_id)
                    user.already_notified_ids = current_list 
                    await session.commit()
                    return True
            return False

    @audit_action(action_type="GET_USER_RECEIVE_NOTIFICATIONS", params_args=[])
    async def get_user_receive_notifications(self, client_source: ClientType, user_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = select(DBUser.receive_notifications).where(DBUser.external_id == str(user_id))
            result = await session.execute(stmt)
            val = result.scalars().first()
            return val if val is not None else False

    @audit_action(action_type="UPDATE_USER_RECEIVE_NOTIFICATIONS", params_args=["status"])
    async def update_user_receive_notifications(self, client_source: ClientType, user_id: str, status: bool) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = update(DBUser).where(DBUser.external_id == str(user_id)).values(receive_notifications=status)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # ---------------------------
    # FAVORITES
    # ---------------------------

    @audit_action(action_type="ADD_FAVORITE", params_args=["type", "item"])
    async def add_favorite(self, client_source: ClientType, user_id: int, type: str, item: FavoriteItem):
        async with AsyncSessionLocal() as session:
            try:
                internal_id = await self._get_user_internal_id(session, user_id)
                if not internal_id:
                    logger.warning(f"Cannot add favorite: User {user_id} not found in DB")
                    return False

                lat = item.coordinates[0] if item.coordinates and len(item.coordinates) > 0 else None
                lon = item.coordinates[1] if item.coordinates and len(item.coordinates) > 1 else None

                new_fav = DBFavorite(
                    user_id=internal_id,
                    transport_type=type.lower(),
                    station_code=item.STATION_CODE,
                    station_name=item.STATION_NAME,
                    station_group_code=item.STATION_GROUP_CODE,
                    line_name=item.LINE_NAME,
                    line_name_with_emoji=item.LINE_NAME_WITH_EMOJI,
                    line_code=item.LINE_CODE,
                    latitude=lat,
                    longitude=lon
                )
                session.add(new_fav)
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding favorite: {e}")
                return False

    @audit_action(action_type="REMOVE_FAVORITE", params_args=["type", "item_id"])
    async def remove_favorite(self, client_source: ClientType, user_id: int, type: str, item_id: str):
        async with AsyncSessionLocal() as session:
            internal_id = await self._get_user_internal_id(session, user_id)
            if not internal_id: return False

            stmt = delete(DBFavorite).where(
                and_(
                    DBFavorite.user_id == internal_id,
                    DBFavorite.transport_type == type.lower(),
                    DBFavorite.station_code == str(item_id)
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    @audit_action(action_type="GET_FAVORITES", params_args=[])
    async def get_favorites_by_user(self, client_source: ClientType, user_id: int) -> List[FavoriteItem]:
        async with AsyncSessionLocal() as session:
            internal_id = await self._get_user_internal_id(session, user_id)
            if not internal_id: return []

            stmt = select(DBFavorite).where(DBFavorite.user_id == internal_id)
            result = await session.execute(stmt)
            db_favs = result.scalars().all()

            fav_items = []
            for f in db_favs:
                fav_items.append(FavoriteItem(
                    USER_ID=str(user_id),
                    TYPE=f.transport_type,
                    STATION_CODE=f.station_code,
                    STATION_NAME=f.station_name,
                    STATION_GROUP_CODE=f.station_group_code or "",
                    LINE_NAME=f.line_name or "",
                    LINE_NAME_WITH_EMOJI=f.line_name_with_emoji or "",
                    LINE_CODE=f.line_code or "",
                    coordinates=[f.latitude or 0, f.longitude or 0] # Revisa el orden aquí también
                ))
            
            return sorted(
                fav_items,
                key=lambda f: self.FAVORITE_TYPE_ORDER.get(f.TYPE, 999)
            )

    async def has_favorite(self, user_id, type, item_id) -> bool:
        async with AsyncSessionLocal() as session:
            internal_id = await self._get_user_internal_id(session, user_id)
            if not internal_id: return False
            
            stmt = select(DBFavorite).where(
                and_(
                    DBFavorite.user_id == internal_id,
                    DBFavorite.transport_type == str(type).lower(),
                    DBFavorite.station_code == str(item_id)
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first() is not None
        
    async def get_active_users_with_favorites(self) -> List[tuple[User, List[FavoriteItem]]]:
        """
        Obtiene usuarios que tienen notificaciones activas Y tienen favoritos.
        Incluye el FCM Token haciendo JOIN con DBUserDevice.
        """
        async with AsyncSessionLocal() as session:
            # 1. MODIFICAMOS LA CONSULTA
            # Añadimos DBUserDevice.token al select
            # Hacemos outerjoin (LEFT JOIN) porque un usuario de Telegram podría no tener device
            stmt = (
                select(DBUser, DBFavorite, DBUserDevice.token) 
                .join(DBFavorite, DBUser.id == DBFavorite.user_id)
                .outerjoin(DBUserDevice, DBUser.id == DBUserDevice.user_id)
                .where(DBUser.receive_notifications == True)
            )
            
            result = await session.execute(stmt)
            rows = result.all()
            
            grouped_data = {}

            # 2. DESEMPAQUETAMOS 3 VALORES (User, Fav, Token)
            for db_user, db_fav, token in rows:
                user_id_ext = db_user.external_id
                
                # Si es la primera vez que vemos al usuario
                if user_id_ext not in grouped_data:
                    domain_user = self._to_domain_user(db_user)
                    
                    # ASIGNAMOS EL TOKEN SI EXISTE
                    # (Si el usuario tiene varios dispositivos, se quedará con el último procesado)
                    if token:
                        domain_user.fcm_token = token

                    grouped_data[user_id_ext] = {
                        "user": domain_user,
                        "favorites": {}, # Usamos un DICT para evitar duplicados temporalmente
                        "seen_favs": set() # Set auxiliar para control
                    }
                
                # ACTUALIZAR TOKEN (Por si apareció en una fila posterior debido al JOIN)
                if token and not grouped_data[user_id_ext]["user"].fcm_token:
                    grouped_data[user_id_ext]["user"].fcm_token = token

                # 3. EVITAR FAVORITOS DUPLICADOS
                # El JOIN con devices multiplica las filas. Si tienes 2 dispositivos, 
                # cada favorito sale 2 veces. Hay que filtrar.
                
                # Usamos STATION_CODE + TYPE como clave única temporal
                fav_unique_key = f"{db_fav.station_code}_{db_fav.transport_type}"
                
                if fav_unique_key not in grouped_data[user_id_ext]["seen_favs"]:
                    domain_fav = self._to_domain_favorite(db_fav, user_id_ext)
                    grouped_data[user_id_ext]["favorites"][fav_unique_key] = domain_fav
                    grouped_data[user_id_ext]["seen_favs"].add(fav_unique_key)

            # 4. CONVERTIR DICT DE FAVORITOS A LISTA
            return [
                (data["user"], list(data["favorites"].values())) 
                for data in grouped_data.values()
            ]

    # El método _to_domain_user lo dejamos igual, ya que asignamos el token "por fuera"
    # para no romper otras partes del código que usen este helper.
    def _to_domain_user(self, db_user: DBUser) -> User:
        return User(
            user_id=db_user.external_id,
            username=db_user.username,
            created_at=db_user.created_at,
            language=db_user.language,
            receive_notifications=db_user.receive_notifications,
            already_notified=db_user.already_notified_ids if db_user.already_notified_ids else [],
            fcm_token="" # Se inicializa vacío, pero el método principal lo sobreescribe
        )

    def _to_domain_favorite(self, f: DBFavorite, user_id_ext: str) -> FavoriteItem:
        return FavoriteItem(
            USER_ID=str(user_id_ext),
            TYPE=f.transport_type,
            STATION_CODE=f.station_code,
            STATION_NAME=f.station_name,
            STATION_GROUP_CODE=f.station_group_code or "",
            LINE_NAME=f.line_name or "",
            LINE_NAME_WITH_EMOJI=f.line_name_with_emoji or "",
            LINE_CODE=f.line_code or "",
            coordinates=[f.latitude or 0, f.longitude or 0]
        )

    # ---------------------------
    # SEARCHES
    # ---------------------------
    async def register_search(self, query: str, user_id_ext: str = None):
        async with AsyncSessionLocal() as session:
            internal_id = None
            if user_id_ext:
                internal_id = await self._get_user_internal_id(session, user_id_ext)
            
            if internal_id:
                new_search = DBSearchHistory(
                    user_id=internal_id,
                    query=query
                )
                session.add(new_search)
                await session.commit()
                return 1
            return 0
        
    async def get_search_history(self, user_id_ext: str) -> List[str]:
        async with AsyncSessionLocal() as session:
            internal_id = await self._get_user_internal_id(session, user_id_ext)
            if not internal_id:
                return []

            stmt = (
                select(DBSearchHistory.query)
                .where(DBSearchHistory.user_id == internal_id)
                .order_by(DBSearchHistory.timestamp.desc())
                .limit(10)
            )
            result = await session.execute(stmt)
            searches = result.scalars().all()
            return searches

    # ---------------------------
    # ALERTS (Service Incidents)
    # ---------------------------

    async def register_alert(self, transport_type: TransportType, api_alert: Alert):
        async with AsyncSessionLocal() as session:
            stmt = select(DBServiceIncident).where(
                and_(
                    DBServiceIncident.external_id == str(api_alert.id),
                    DBServiceIncident.transport_type == transport_type.value
                )
            )
            result = await session.execute(stmt)
            exists = result.scalars().first()

            if exists:
                return False

            new_incident = DBServiceIncident(
                external_id=str(api_alert.id),
                transport_type=transport_type.value,
                begin_date=api_alert.begin_date,
                end_date=api_alert.end_date,
                status=api_alert.status,
                cause=api_alert.cause,
                publications=[pub.__dict__ for pub in api_alert.publications],
                affected_entities=[ent.__dict__ for ent in api_alert.affected_entities]
            )
            session.add(new_incident)
            await session.commit()
            logger.info(f"New ServiceIncident registered: {api_alert.id}")
            return True

    async def get_alerts(self, only_active: bool = True) -> List[Alert]:
        async with AsyncSessionLocal() as session:
            stmt = select(DBServiceIncident)

            if only_active:
                now = datetime.now()
                stmt = stmt.where(
                    (DBServiceIncident.end_date == None) | 
                    (DBServiceIncident.end_date > now)
                )
            result = await session.execute(stmt)
            db_alerts = result.scalars().all()

            domain_alerts = []
            for a in db_alerts:
                pubs = [Publication(**p) for p in (a.publications or [])]
                ents = [AffectedEntity(**e) for e in (a.affected_entities or [])]

                domain_alerts.append(Alert(
                    id=a.external_id,
                    transport_type=TransportType(a.transport_type) if a.transport_type else None,
                    begin_date=a.begin_date,
                    end_date=a.end_date,
                    status=a.status,
                    cause=a.cause,
                    publications=pubs,
                    affected_entities=ents
                ))
            return domain_alerts
        

    # AUDIT
    @audit_action(action_type="NOTIFICATION", params_args=["alert"])
    async def register_notification(self, client_source: ClientType, user_id: str, alert: Alert):
        pass