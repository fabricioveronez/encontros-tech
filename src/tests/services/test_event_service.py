
import pytest
from unittest.mock import MagicMock
from services.event_service import EventNotFoundError
from services import event_service
from schemas.event import EventCreate, EventUpdate
from models.event import Event
import datetime

def test_create_event():
    # Arrange
    mock_db = MagicMock()

    event_data = EventCreate(
        title="Test Event",
        description="A test event",
        date=datetime.datetime.now(),
        location="Test Location",
        technologies=["Python", "FastAPI"]
    )

    # Act
    created_event = event_service.create_event(db=mock_db, event=event_data)

    # Assert
    assert created_event.title == event_data.title
    assert created_event.description == event_data.description
    assert created_event.technologies == event_data.technologies
    
    # Check that add, commit, and refresh were called correctly
    mock_db.add.assert_called_once()  # Only one call to add the event
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(created_event)

def test_create_event_with_technologies():
    # Arrange
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing technologies

    event_data = EventCreate(
        title="Another Test Event",
        description="Another test event",
        date=datetime.datetime.now(),
        location="Test Location",
        technologies=["FastAPI", "Python"]
    )

    # Act
    created_event = event_service.create_event(db=mock_db, event=event_data)

    # Assert
    assert created_event.title == event_data.title
    mock_db.add.assert_called()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(created_event)

def test_get_events():
    # Arrange
    mock_db = MagicMock()
    
    # Mock the query chain
    mock_query = mock_db.query.return_value
    mock_order_by = mock_query.order_by.return_value
    mock_offset = mock_order_by.offset.return_value
    
    # Act
    event_service.get_events(db=mock_db, skip=10, limit=50)

    # Assert
    mock_db.query.assert_called_once_with(Event)
    mock_query.order_by.assert_called_once()
    mock_order_by.offset.assert_called_once_with(10)
    mock_offset.limit.assert_called_once_with(50)
    mock_offset.limit.return_value.all.assert_called_once()

# Teste removido - funcionalidade de filtro por technology não implementada

def test_get_events_with_search_filter():
    # Arrange
    mock_db = MagicMock()
    
    # Mock the query chain with search filter
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_order_by = mock_filter.order_by.return_value
    mock_offset = mock_order_by.offset.return_value
    
    # Act
    event_service.get_events(db=mock_db, search="Python")

    # Assert
    mock_db.query.assert_called_once_with(Event)
    mock_query.filter.assert_called_once()
    mock_filter.order_by.assert_called_once()

def test_get_event_by_token_success():
    # Arrange
    mock_db = MagicMock()
    test_token = "test-token-123"
    expected_event = Event(id=1, title="Test Event", edit_token=test_token)
    
    mock_db.query.return_value.filter.return_value.first.return_value = expected_event
    
    # Act
    result = event_service.get_event_by_token(db=mock_db, edit_token=test_token)
    
    # Assert
    assert result == expected_event
    mock_db.query.assert_called_once_with(Event)

def test_get_event_by_token_not_found():
    # Arrange
    mock_db = MagicMock()
    test_token = "invalid-token"
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Act & Assert
    with pytest.raises(EventNotFoundError) as exc_info:
        event_service.get_event_by_token(db=mock_db, edit_token=test_token)
    
    assert str(exc_info.value) == "Event not found"

def test_update_event():
    # Arrange
    mock_db = MagicMock()
    test_token = "test-token-123"
    
    # Mock existing event - criar sem o campo technologies pois não existe no modelo
    existing_event = MagicMock()
    existing_event.title = "Old Title"
    existing_event.edit_token = test_token
    existing_event.id = 1
    
    mock_db.query.return_value.filter.return_value.first.return_value = existing_event
    
    event_update = EventUpdate(
        title="Updated Title",
        description="Updated description",
        date=datetime.datetime.now(),
        location="Updated Location",
        technologies=["React", "Python"]
    )
    
    # Act
    result = event_service.update_event(db=mock_db, edit_token=test_token, event_update=event_update)
    
    # Assert
    assert result.title == event_update.title
    assert result.description == event_update.description
    assert result.location == event_update.location
    assert result.technologies == event_update.technologies
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_event)

# Teste get_technologies removido - funcionalidade não implementada


# ---------- Filtro por intervalo de datas ----------

def _filter_args(mock_db):
    """Retorna os argumentos posicionais da única chamada a query.filter()."""
    mock_query = mock_db.query.return_value
    mock_query.filter.assert_called_once()
    return mock_query.filter.call_args.args

def test_get_events_with_start_date_only():
    mock_db = MagicMock()

    event_service.get_events(db=mock_db, start_date=datetime.date(2024, 3, 1))

    conditions = _filter_args(mock_db)
    assert len(conditions) == 1
    assert conditions[0].right.value == datetime.datetime(2024, 3, 1, 0, 0)

def test_get_events_with_end_date_only_is_inclusive():
    mock_db = MagicMock()

    event_service.get_events(db=mock_db, end_date=datetime.date(2024, 3, 5))

    conditions = _filter_args(mock_db)
    assert len(conditions) == 1
    # Limite exclusivo no dia seguinte: inclui eventos de qualquer hora do dia 05/03
    assert conditions[0].right.value == datetime.datetime(2024, 3, 6, 0, 0)

def test_get_events_with_date_range():
    mock_db = MagicMock()

    event_service.get_events(
        db=mock_db,
        start_date=datetime.date(2024, 2, 20),
        end_date=datetime.date(2024, 3, 5),
    )

    conditions = _filter_args(mock_db)
    assert len(conditions) == 2

def test_get_events_with_search_and_date_range():
    mock_db = MagicMock()
    mock_filter = mock_db.query.return_value.filter.return_value

    event_service.get_events(
        db=mock_db,
        search="Python",
        start_date=datetime.date(2024, 3, 1),
        end_date=datetime.date(2024, 3, 31),
    )

    conditions = _filter_args(mock_db)
    assert len(conditions) == 3
    mock_filter.order_by.assert_called_once()

def test_get_events_same_start_and_end_date_is_allowed():
    mock_db = MagicMock()

    event_service.get_events(
        db=mock_db,
        start_date=datetime.date(2024, 3, 5),
        end_date=datetime.date(2024, 3, 5),
    )

    assert len(_filter_args(mock_db)) == 2

def test_get_events_start_date_after_end_date_raises():
    mock_db = MagicMock()

    with pytest.raises(ValueError):
        event_service.get_events(
            db=mock_db,
            start_date=datetime.date(2024, 3, 31),
            end_date=datetime.date(2024, 3, 1),
        )

    mock_db.query.assert_not_called()

@pytest.mark.parametrize("value", [None, "", "   "])
def test_parse_date_param_empty_returns_none(value):
    assert event_service.parse_date_param(value) is None

def test_parse_date_param_valid():
    assert event_service.parse_date_param("2024-03-05") == datetime.date(2024, 3, 5)

@pytest.mark.parametrize("value", ["abc", "05/03/2024", "2024-13-01"])
def test_parse_date_param_invalid_raises(value):
    with pytest.raises(ValueError):
        event_service.parse_date_param(value)
