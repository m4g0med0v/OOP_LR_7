import os
import sqlite3
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.individual_task_1 import (
    ConnectError,
    Train,
    add_train,
    connect_db,
    find_train,
    list_trains,
    load_from_xml,
    save_to_xml,
)


class TestTrainManagement(unittest.TestCase):
    def setUp(self):
        """Создает временную базу данных перед каждым тестом."""
        self.db_name = "test_trains"
        self.conn = connect_db(self.db_name)
        self.test_data = [
            Train("001A", "Moscow", "10:30", "Leningradsky"),
            Train("002B", "Saint Petersburg", "14:00", "Moscow"),
        ]

    def tearDown(self):
        """Удаляет временную базу данных после каждого теста."""
        self.conn.close()
        db_path = f"data/{self.db_name}.db"
        if os.path.exists(db_path):
            os.remove(db_path)

    def test_connect_db(self):
        """Проверяет успешное подключение к базе данных."""
        self.assertIsInstance(self.conn, sqlite3.Connection)

    def test_add_train(self):
        """Тестирует добавление нового поезда в базу данных."""
        train = self.test_data[0]
        result = add_train(
            self.conn,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], train.number)

    def test_add_duplicate_train(self):
        """Проверяет попытку добавления дублирующего номера поезда."""
        train = self.test_data[0]
        add_train(
            self.conn,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        result = add_train(
            self.conn,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        self.assertIsNone(result)

    def test_list_trains(self):
        """Проверяет извлечение всех поездов из базы данных."""
        for train in self.test_data:
            add_train(
                self.conn,
                train.destination,
                train.number,
                train.time,
                train.station_name,
            )
        trains = list_trains(self.conn)
        self.assertEqual(len(trains), len(self.test_data))
        self.assertEqual(trains[0].number, self.test_data[0].number)

    def test_find_train(self):
        """Тестирует поиск поезда по номеру."""
        train = self.test_data[0]
        add_train(
            self.conn,
            train.destination,
            train.number,
            train.time,
            train.station_name,
        )
        result = find_train(self.conn, train.number)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], train.number)

    def test_save_to_xml(self):
        """Тестирует сохранение поездов в XML-файл."""
        filename = "test_trains.xml"
        save_to_xml(self.test_data, filename)
        self.assertTrue(Path(filename).exists())
        tree = ET.parse(filename)
        root = tree.getroot()
        self.assertEqual(len(root.findall("train")), len(self.test_data))
        os.remove(filename)

    def test_load_from_xml(self):
        """Тестирует загрузку поездов из XML-файла."""
        filename = "test_trains.xml"
        save_to_xml(self.test_data, filename)
        loaded_trains = load_from_xml(filename)
        self.assertEqual(len(loaded_trains), len(self.test_data))
        self.assertEqual(loaded_trains[0].number, self.test_data[0].number)
        os.remove(filename)

    def test_connection_error(self):
        """Проверяет обработку ошибки подключения."""
        with self.assertRaises(ConnectError):
            connect_db("nonexistent_path/test")
