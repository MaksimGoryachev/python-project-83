import logging

import validators
from bs4 import BeautifulSoup
from flask import (
    flash,
    get_flashed_messages,
)


def get_tag_content(resp):
    """Получает контент тега H1, заголовка страницы и описания."""
    soup = BeautifulSoup(resp.text, 'html.parser')

    h1_tag = soup.find('h1')
    h1 = h1_tag.text.strip() if h1_tag else ''
    logging.info('Содержимое тега H1: "%s"', h1)

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''
    logging.info('Содержимое тега Title: "%s"', title)

    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'].strip() if description_tag else ''
    logging.info('Содержимое тега Description: "%s"', description)

    return h1, title, description


def validate(url_from_request: str) -> list:
    """Валидация URL."""
    if len(url_from_request) > 255:
        flash('URL превышает 255 символов', 'danger')
    elif not validators.url(url_from_request):
        flash('Некорректный URL', 'danger')
    return get_flashed_messages(category_filter='danger')
