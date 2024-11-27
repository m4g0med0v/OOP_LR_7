import os

import pytest

from src.individual_task_1 import (
    Train,
    connect_db,
)


@pytest.fixture(scope="session")
def setup_db():
    """Создает временную базу данных перед каждым тестом."""
    db_name = "test_trains"
    conn = connect_db(db_name)
    yield conn
    conn.close()
    db_path = f"data/{db_name}.db"
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def test_data():
    """Возвращает тестовые данные поездов."""
    return [
        Train("001A", "Moscow", "10:30", "Leningradsky"),
        Train("002B", "Saint Petersburg", "14:00", "Moscow"),
    ]
