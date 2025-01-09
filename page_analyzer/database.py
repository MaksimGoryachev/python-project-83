import logging
from datetime import datetime
from typing import Dict, List, Tuple

import psycopg2
from psycopg2.extras import DictCursor

from page_analyzer.config import DATABASE_URL


def get_connection() -> psycopg2.extensions.connection | None:
    """Создает и возвращает новое соединение с базой данных."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logging.info('Соединение с базой данных успешно установлено')
        return conn
    except psycopg2.OperationalError as e:
        logging.exception('Ошибка при установлении соединения: %s', e)
        return None
    except Exception as e:
        logging.exception('Произошла неожиданная ошибка: %s', e)
        return None


def close_connection(connection: psycopg2.extensions.connection) -> None:
    """Закрывает соединение с базой данных."""
    if connection:
        try:
            connection.close()
            logging.info('Соединение с базой данных закрыто')
        except psycopg2.Error as e:
            logging.exception('Ошибка при закрытии соединения: %s', e)
        except Exception as e:
            logging.exception('Произошла неожиданная ошибка: %s', e)


def commit_transaction(conn: psycopg2.extensions.connection) -> None:
    """Коммитит изменения в базе данных."""
    if conn:
        try:
            conn.commit()
            logging.info('Изменения успешно зафиксированы в базе данных')
        except psycopg2.Error as e:
            logging.exception('Ошибка при фиксации изменений: %s', e)


def create_url_check(conn: psycopg2.extensions.connection,
                     params: Tuple) -> bool:
    """Создает запись в таблице url_checks."""
    query_insert = (
        'INSERT INTO url_checks (url_id, status_code, h1, title,'
        ' description, created_at)'
        'VALUES (%s, %s, %s, %s, %s, %s)'
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(query_insert, params)
            return True
    except psycopg2.Error as e:
        logging.error('Произошла ошибка при выполнении запроса:  "%s"', e)
        return False


def create_url(name: str,
               conn: psycopg2.extensions.connection) -> int | None:
    """Создает новую запись в таблице urls и возвращает её ID."""
    query_insert = ('INSERT INTO urls (name, created_at) '
                    'VALUES (%s, %s) RETURNING id')

    try:
        with conn.cursor() as cursor:
            cursor.execute(query_insert, (name, datetime.now().date()))
            new_url_id = cursor.fetchone()
            return new_url_id[0] if new_url_id else None

    except psycopg2.Error as e:
        logging.exception('Ошибка при добавлении страницы: "%s"', e)
        return None


def get_url_by_name(name,
                    conn: psycopg2.extensions.connection) -> int | None:
    """Проверяет, существует ли запись в таблице urls и возвращает её ID."""
    query_check = 'SELECT id FROM urls WHERE name = %s LIMIT 1'

    try:
        with conn.cursor() as cursor:
            cursor.execute(query_check, (name,))
            existing_url = cursor.fetchone()
            return existing_url[0] if existing_url else None

    except psycopg2.Error as e:
        logging.exception('Ошибка при проверке ID страницы: "%s"', e)
        return None


def get_url_by_id(url_id: int,
                  conn: psycopg2.extensions.connection) -> Dict | None:
    """Возвращает данные по указанной странице."""
    query = 'SELECT * FROM urls WHERE id = %s'

    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (url_id,))
            row = cursor.fetchone()
            if row is not None:
                return dict(row)
        return None
    except psycopg2.Error as e:
        logging.exception('Ошибка при получении данных страницы: "%s"', e)
        return None


def get_all_urls(conn: psycopg2.extensions.connection) -> List[Dict]:
    """Возвращает список всех добавленных страниц."""
    query = """
    SELECT urls.id, urls.name,
    MAX(url_checks.created_at) AS last_check_date,
    MAX(url_checks.status_code) AS last_status_code
    FROM urls
    LEFT JOIN url_checks ON urls.id = url_checks.url_id
    GROUP BY urls.id
    ORDER BY urls.id DESC;
    """

    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            urls = [
                {
                    'id': row['id'],
                    'name': row['name'],
                    'last_check_date': row['last_check_date'] or None,
                    'last_status_code': row['last_status_code'] or None
                }
                for row in rows
            ]
            return urls

    except psycopg2.Error as e:
        logging.exception('Произошла ошибка при получении списка URL: "%s"', e)
        return []


def get_data_checks(url_id: int,
                    conn: psycopg2.extensions.connection
                    ) -> List[Dict] | None:
    """Возвращает список всех проверок для указанной страницы."""
    checks_query = (
        'SELECT * FROM url_checks '
        'WHERE url_id = %s ORDER BY id DESC'
    )
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(checks_query, (url_id,))
            data = cursor.fetchall()
            if data:
                checks_data = [dict(row) for row in data]
                return checks_data
        return None
    except psycopg2.Error as e:
        logging.exception('Ошибка при получении данных'
                          ' проверки страницы: "%s"', e)
        return None
