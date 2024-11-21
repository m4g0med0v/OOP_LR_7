#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Выполнить индивидуальное задание лабораторной работы 4.5,
# использовав классы данных, а также загрузку и сохранение данных в формат XML.


import argparse
import logging
import os
import sqlite3
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple


class ConnectError(Exception): ...


# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format=(
        "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d"
        " %(levelname)-7s - %(message)s"
    ),
)


@dataclass
class Train:
    number: str
    destination: str
    time: str
    station_name: str


def connect_db(db_name: str) -> sqlite3.Connection:
    try:
        if not Path("data/").exists():
            os.mkdir("data")
        conn = sqlite3.connect(f"data/{db_name}.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destination TEXT NOT NULL,
                number TEXT NOT NULL UNIQUE,
                time TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT NOT NULL,
                train_id INTEGER,
                FOREIGN KEY (train_id) REFERENCES trains(id)
            )
        """)

        conn.commit()
        logging.info("Соединение с базой данных успешно установлено.")
        return conn
    except Exception as e:
        logging.error("Ошибка при подключении к базе данных: %s", e)
        raise ConnectError()


def save_to_xml(trains: List[Train], filename: str) -> None:
    root = ET.Element("trains")
    for train in trains:
        train_elem = ET.SubElement(root, "train")
        for field, value in asdict(train).items():
            ET.SubElement(train_elem, field).text = value
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    logging.info(f"Данные сохранены в файл {filename}")


def load_from_xml(filename: str) -> List[Train]:
    trains = []
    tree = ET.parse(filename)
    root = tree.getroot()
    for train_elem in root.findall("train"):
        train_data = {child.tag: child.text for child in train_elem}
        trains.append(Train(**train_data))  # type: ignore[arg-type]
    logging.info(f"Данные загружены из файла {filename}")
    return trains


def add_train(
    conn: sqlite3.Connection,
    destination: str,
    number: str,
    time: str,
    station_name: str,
) -> Optional[Tuple[str, str, str, str]]:
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trains (destination, number, time) VALUES (?, ?, ?)",
            (destination, number, time),
        )
        train_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO stations (station_name, train_id) VALUES (?, ?)",
            (station_name, train_id),
        )

        conn.commit()
        logging.info(
            "Добавлен поезд №%s, пункт назначения: %s, время отправления: %s.",
            number,
            destination,
            time,
        )
        return find_train(conn, number)
    except sqlite3.IntegrityError:
        logging.error("Поезд с номером %s уже существует.", number)
        print(f"Ошибка: поезд с номером {number} уже существует.")
    except Exception as e:
        logging.error("Ошибка при добавлении поезда: %s", e)
        print(f"Ошибка при добавлении поезда: {e}")
    return None


def list_trains(
    conn: sqlite3.Connection,
) -> List[Train]:
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trains.number, trains.destination, trains.time, stations.station_name
            FROM trains
            LEFT JOIN stations ON trains.id = stations.train_id
        """)

        rows = cursor.fetchall()
        if rows:
            logging.info("Список поездов успешно извлечен.")
            return [Train(*row) for row in rows]
        else:
            logging.info("Список поездов пуст.")
            return []
    except Exception as e:
        logging.error("Ошибка при получении списка поездов: %s", e)
        print(f"Ошибка при получении списка поездов: {e}")
    return []


def find_train(
    conn: sqlite3.Connection, number: str
) -> Optional[Tuple[str, str, str, str]]:
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT trains.number, trains.destination, trains.time, stations.station_name
            FROM trains
            LEFT JOIN stations ON trains.id = stations.train_id
            WHERE trains.number = ?
        """,
            (number,),
        )

        train = cursor.fetchone()
        if isinstance(train, tuple) and len(train) == 4:
            logging.info("Поиск поезда №%s завершен.", number)
            return train  # Успешный результат
        else:
            logging.info("Поезд №%s не найден.", number)
            return None
    except Exception as e:
        logging.error("Ошибка при поиске поезда №%s: %s", number, e)
        print(f"Ошибка при поиске поезда: {e}")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Управление списком поездов")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Команды")

    add_parser = subparsers.add_parser("add", help="Добавить новый поезд")
    add_parser.add_argument(
        "-d", "--destination", required=True, help="Название пункта назначения"
    )
    add_parser.add_argument("-n", "--number", required=True, help="Номер поезда")
    add_parser.add_argument(
        "-t", "--time", required=True, help="Время отправления (чч:мм)"
    )
    add_parser.add_argument("-s", "--station", required=True, help="Название станции")

    subparsers.add_parser("list", help="Показать все поезда")

    find_parser = subparsers.add_parser("find", help="Найти поезд по номеру")
    find_parser.add_argument("number", help="Номер поезда для поиска")

    save_parser = subparsers.add_parser("save-xml", help="Сохранить данные в XML-файл")
    save_parser.add_argument("file", help="Путь к XML-файлу")

    load_parser = subparsers.add_parser(
        "load-xml", help="Загрузить данные из XML-файла"
    )
    load_parser.add_argument("file", help="Путь к XML-файлу")

    args = parser.parse_args()

    try:
        conn = connect_db("trains")

        if args.command == "add":
            ans = add_train(
                conn, args.destination, args.number, args.time, args.station
            )
            if ans:
                print(f"Поезд №{ans[0]} в {ans[1]} добавлен.")

        if args.command == "list":
            trains = list_trains(conn)
            if trains:
                for train in trains:
                    print(
                        f"Поезд №{train.number} отправляется в {train.destination} "
                        f"в {train.time}, станция: {train.station_name}."
                    )
            else:
                print("Нет данных о поездах.")

        if args.command == "find":
            ans = find_train(conn, args.number)
            if ans:
                print(
                    f"Поезд №{ans[0]} отправляется в {ans[1]} в {ans[2]},"
                    " станция: {ans[3]}."
                )
            else:
                print(f"Поезд с номером {args.number} не найден.")

        if args.command == "save-xml":
            trains = list_trains(conn)
            save_to_xml(trains, args.file)
            print(f"Данные сохранены в файл {args.file}.")

        if args.command == "load-xml":
            trains = load_from_xml(args.file)
            for train in trains:
                add_train(
                    conn,
                    train.destination,
                    train.number,
                    train.time,
                    train.station_name,
                )
            print(f"Данные из файла {args.file} загружены в базу данных.")

        conn.close()
    except Exception as e:
        logging.error("Необработанная ошибка: %s", e)
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
