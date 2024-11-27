import os
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from src.individual_task_1 import (
    ConnectError,
    add_train,
    connect_db,
    find_train,
    list_trains,
    load_from_xml,
    save_to_xml,
)


class TestTrainManagement:
    def test_connect_db(self, setup_db):
        """Проверяет успешное подключение к базе данных."""
        conn = setup_db
        assert isinstance(conn, sqlite3.Connection)

    def test_add_train(self, setup_db, test_data):
        """Тестирует добавление нового поезда в базу данных."""
        train = test_data[0]
        result = add_train(
            setup_db,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        assert result is not None
        assert result[0] == train.number

    def test_add_duplicate_train(self, setup_db, test_data):
        """Проверяет попытку добавления дублирующего номера поезда."""
        train = test_data[0]
        add_train(
            setup_db,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        result = add_train(
            setup_db,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        assert result is None

    def test_list_trains(self, setup_db, test_data):
        """Проверяет извлечение всех поездов из базы данных."""
        for train in test_data:
            add_train(
                setup_db,
                train.destination,
                train.number,
                train.time,
                train.station_name,
            )
        trains = list_trains(setup_db)
        assert len(trains) == len(test_data)
        assert trains[0].number == test_data[0].number

    def test_find_train(self, setup_db, test_data):
        """Тестирует поиск поезда по номеру."""
        train = test_data[0]
        add_train(
            setup_db,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        result = find_train(setup_db, train.number)
        assert result is not None
        assert result[0] == train.number

    def test_save_to_xml(self, test_data):
        """Тестирует сохранение поездов в XML-файл."""
        filename = "test_trains.xml"
        save_to_xml(test_data, filename)
        assert Path(filename).exists()
        tree = ET.parse(filename)
        root = tree.getroot()
        assert len(root.findall("train")) == len(test_data)
        os.remove(filename)

    def test_load_from_xml(self, test_data):
        """Тестирует загрузку поездов из XML-файла."""
        filename = "test_trains.xml"
        save_to_xml(test_data, filename)
        loaded_trains = load_from_xml(filename)
        assert len(loaded_trains) == len(test_data)
        assert loaded_trains[0].number == test_data[0].number
        os.remove(filename)

    def test_connection_error(self):
        """Проверяет обработку ошибки подключения."""
        with pytest.raises(ConnectError):
            connect_db("nonexistent_path/test")
