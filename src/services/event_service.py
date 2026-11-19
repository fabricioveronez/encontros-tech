from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.event import Event
from schemas.event import EventCreate, EventUpdate
from typing import List, Optional
import datetime
from core.logging import get_logger, log_database_operation, log_business_event

logger = get_logger("event_service")

class EventNotFoundError(Exception):
    pass

def create_event(db: Session, event: EventCreate):
    logger.info(f"Criando novo evento: {event.title}")
    
    try:
        db_event = Event(
            title=event.title, 
            description=event.description, 
            date=event.date, 
            location=event.location
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        # Por enquanto, não persistimos technologies no banco, apenas retornamos no objeto
        db_event.technologies = event.technologies
        
        log_database_operation(logger, "CREATE", "events", f"id={db_event.id}")
        log_business_event(logger, "EVENT_CREATED", {
            "event_id": db_event.id,
            "title": event.title,
            "location": event.location,
            "technologies_count": len(event.technologies)
        })
        
        logger.info(f"Evento criado com sucesso: ID={db_event.id}, Token={db_event.edit_token}")
        return db_event
        
    except Exception as e:
        logger.error(f"Erro ao criar evento: {str(e)}")
        db.rollback()
        raise

def parse_date_param(value: Optional[str]) -> Optional[datetime.date]:
    """Converte um parâmetro de data (YYYY-MM-DD) em date; vazio ou None vira None.

    Lança ValueError se o formato for inválido.
    """
    if value is None or not value.strip():
        return None
    try:
        return datetime.date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f"Data inválida: '{value}'. Use o formato AAAA-MM-DD.")

def get_events(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
):
    logger.debug(
        f"Buscando eventos: skip={skip}, limit={limit}, search={search}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    if start_date and end_date and start_date > end_date:
        raise ValueError("A data inicial não pode ser maior que a data final.")

    try:
        query = db.query(Event)
        conditions = []

        if search:
            conditions.append(or_(
                Event.title.ilike(f"%{search}%"),
                Event.description.ilike(f"%{search}%"),
                Event.location.ilike(f"%{search}%")
            ))
            logger.debug(f"Aplicando filtro de busca: {search}")

        # Intervalo inclusivo por dia: [start_date 00:00, end_date + 1 dia 00:00)
        if start_date:
            conditions.append(Event.date >= datetime.datetime.combine(start_date, datetime.time.min))
        if end_date:
            conditions.append(Event.date < datetime.datetime.combine(end_date + datetime.timedelta(days=1), datetime.time.min))
        if start_date or end_date:
            logger.debug(f"Aplicando filtro de data: {start_date} até {end_date}")

        if conditions:
            query = query.filter(*conditions)

        query = query.order_by(Event.date)
        events = query.offset(skip).limit(limit).all()
        
        log_database_operation(logger, "READ", "events", f"count={len(events)}")
        logger.info(f"Retornando {len(events)} evento(s)")
        
        return events
        
    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {str(e)}")
        raise

def get_event_by_token(db: Session, edit_token: str):
    logger.debug(f"Buscando evento por token: {edit_token[:8]}...")
    
    try:
        event = db.query(Event).filter(Event.edit_token == edit_token).first()
        if not event:
            logger.warning(f"Evento não encontrado para token: {edit_token[:8]}...")
            raise EventNotFoundError("Event not found")
        
        log_database_operation(logger, "READ", "events", f"id={event.id} by_token")
        logger.info(f"Evento encontrado: ID={event.id}, Título={event.title}")
        return event
        
    except EventNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar evento por token: {str(e)}")
        raise

def get_event(db: Session, event_id: int):
    logger.debug(f"Buscando evento por ID: {event_id}")
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            logger.warning(f"Evento não encontrado para ID: {event_id}")
            raise EventNotFoundError("Event not found")
        
        log_database_operation(logger, "READ", "events", f"id={event_id}")
        logger.info(f"Evento encontrado: ID={event.id}, Título={event.title}")
        return event
        
    except EventNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar evento por ID: {str(e)}")
        raise

def update_event(db: Session, edit_token: str, event_update: EventUpdate):
    logger.info(f"Atualizando evento com token: {edit_token[:8]}...")
    
    try:
        db_event = get_event_by_token(db, edit_token)
        old_title = db_event.title
        
        db_event.title = event_update.title
        db_event.description = event_update.description
        db_event.date = event_update.date
        db_event.location = event_update.location
        
        db.commit()
        db.refresh(db_event)
        
        # Por enquanto, não persistimos technologies no banco, apenas retornamos no objeto
        db_event.technologies = event_update.technologies
        
        log_database_operation(logger, "UPDATE", "events", f"id={db_event.id}")
        log_business_event(logger, "EVENT_UPDATED", {
            "event_id": db_event.id,
            "old_title": old_title,
            "new_title": event_update.title,
            "location": event_update.location,
            "technologies_count": len(event_update.technologies)
        })
        
        logger.info(f"Evento atualizado com sucesso: ID={db_event.id}")
        return db_event
        
    except Exception as e:
        logger.error(f"Erro ao atualizar evento: {str(e)}")
        db.rollback()
        raise
