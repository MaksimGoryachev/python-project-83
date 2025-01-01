import logging
from typing import Dict, List, Optional

import psycopg2

from page_analyzer.config import DATABASE_URL


def get_connection() -> psycopg2.extensions.connection:
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
        except Exception as e:
            logging.exception('Ошибка при закрытии соединения: %s', e)


def create_url_check(conn: psycopg2.extensions.connection, params) -> bool:
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


def create_url(params,
               conn: psycopg2.extensions.connection) -> int | None:
    """Создает новую запись в таблице urls и возвращает её ID."""
    query_insert = ('INSERT INTO urls (name, created_at) '
                    'VALUES (%s, %s) RETURNING id')

    try:
        with conn.cursor() as cursor:
            cursor.execute(query_insert, params)
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
                  conn: psycopg2.extensions.connection) -> Optional[Dict]:
    """Возвращает данные по указанной странице."""
    query = (
        'SELECT * FROM urls WHERE id = %s'
    )
    url_data = {}
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (url_id,))
            row = cursor.fetchone()
            if row is not None:
                url_data = {
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2]
                }
        return url_data
    except psycopg2.Error as e:
        logging.exception('Ошибка при получении данных страницы: "%s"', e)
        return None


def get_all_urls(conn: psycopg2.extensions.connection) -> list:
    """Возвращает список всех добавленных страниц."""
    query = """
    SELECT DISTINCT ON (urls.id) urls.id, urls.name,
    MAX(url_checks.created_at), url_checks.status_code
    FROM urls
    LEFT JOIN url_checks ON urls.id = url_checks.url_id
    GROUP BY urls.id, url_checks.status_code, url_checks.created_at
    ORDER BY urls.id DESC, url_checks.created_at DESC;
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            urls = [
                {
                    'id': row[0],
                    'name': row[1],
                    'last_check_date': row[2] or '',
                    'last_status_code': row[3] or ''
                }
                for row in rows
            ]
            return urls

    except psycopg2.Error as e:
        logging.exception('Произошла ошибка при получении списка URL: "%s"', e)
        return []


def get_data_checks(url_id: int,
                    conn: psycopg2.extensions.connection
                    ) -> Optional[List[Dict]]:
    """Возвращает список всех проверок для указанной страницы."""
    checks_query = (
        'SELECT * FROM url_checks '
        'WHERE url_id = %s ORDER BY id DESC'
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(checks_query, (url_id,))
            data = cursor.fetchall()
            if data:
                checks_data = [
                    {
                        'id': row[0],
                        'status_code': row[2],
                        'h1': row[3],
                        'title': row[4],
                        'description': row[5],
                        'created_at': row[6]
                    }
                    for row in data
                ]
                return checks_data
        return None
    except psycopg2.Error as e:
        logging.exception('Ошибка при получении данных'
                          ' проверки страницы: "%s"', e)
        return None
