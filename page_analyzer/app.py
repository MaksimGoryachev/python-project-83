import logging
import os

import psycopg2
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from page_analyzer.database import (
    create_new_url,
    create_url_check,
    get_all_urls,
    get_data_checks,
    get_one_url,
)
from page_analyzer.logging_config import setup_logging
from page_analyzer.tools import validate

load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    """Возвращает главную страницу."""
    return render_template('base.html')


@app.get('/urls')
def get_urls():
    """Возвращает страницу со списком всех сайтов."""
    try:
        urls = get_all_urls()
        return render_template('urls.html', urls=urls)
    except psycopg2.errors as e:
        logging.exception('Произошла ошибка при получении списка URL: "%s"', e)
        flash(f'Ошибка при получении списка страниц: {e}', 'danger')
        return render_template('urls.html', urls=[])


@app.get('/urls/<int:url_id>')
def get_url_id(url_id):
    """Возвращает страницу с полной информацией."""
    url_data = get_one_url(url_id)
    try:
        if url_data is None:
            abort(404)
        checks_url = get_data_checks(url_id)
        return render_template(
            'url.html',
            checks_url=checks_url,
            url=url_data
        )
    except Exception as e:
        logging.exception('Произошла ошибка при получении данных URL: "%s"', e)
        abort(500)


@app.post('/urls')
def add_url():
    """Добавление новой страницы."""
    url_from_request = request.form.get('url', '')
    errors = validate(url_from_request)

    if errors:
        logging.error('Ошибка валидации URL')
        return render_template(
            'base.html',
            url_from_request=url_from_request
        ), 422
    url_id = create_new_url(url_from_request)

    if url_id is None:
        logging.error('Ошибка сохранения в базу')
        return render_template(
            'base.html',
            url_from_request=url_from_request,
        ), 422
    return redirect(url_for('get_url_id', url_id=url_id), 302)


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    """Проверка статуса страницы."""
    result = create_url_check(url_id)
    if result is None:
        flash('Прооизошла ошибка при проверке', 'danger')
    else:
        flash('Страница успешно проверена', 'success')

    return redirect(url_for('get_url_id', url_id=url_id))


@app.errorhandler(404)
def page_not_found(error):
    """Обработчик ошибки 404."""
    logging.exception(error)
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Обработчик ошибки 500."""
    logging.exception(error)
    return render_template('500.html'), 500


if __name__ == '__main__':
    setup_logging()
    logging.info("Приложение запущено")
    app.run(debug=True)
