import logging
import os
from datetime import datetime

import requests
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
from werkzeug.exceptions import HTTPException

from page_analyzer.config import setup_logging
from page_analyzer.database import (
    close_connection,
    create_url,
    create_url_check,
    get_all_urls,
    get_connection,
    get_data_checks,
    get_url_by_id,
    get_url_by_name,
)
from page_analyzer.tools import (
    get_response,
    get_scheme_hostname,
    get_tag_content,
    validate,
)

load_dotenv()
setup_logging()
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    """Возвращает главную страницу."""
    return render_template('base.html')


@app.get('/urls')
def get_urls():
    """Возвращает страницу со списком всех сайтов."""
    conn = get_connection()
    urls = get_all_urls(conn)
    close_connection(conn)
    return render_template('urls.html', urls=urls)


@app.get('/urls/<int:url_id>')
def get_url_id(url_id: int):
    """Возвращает страницу с полной информацией."""
    conn = get_connection()
    url_data = get_url_by_id(url_id, conn)
    try:
        if url_data is None:
            abort(404)
        checks_url = get_data_checks(url_id, conn)
        return render_template(
            'url.html',
            checks_url=checks_url,
            url=url_data
        )
    except HTTPException as e:
        logging.exception('Произошла HTTP ошибка'
                          ' при получении данных URL: "%s"', e)
        abort(500)
    finally:
        close_connection(conn)


@app.post('/urls')
def add_url() -> tuple:
    """Добавление новой страницы."""
    url_from_request = request.form.get('url', '')

    if not validate(url_from_request):
        flash('Некорректный URL', 'danger')
        return render_template(
            'base.html',
            url_from_request=url_from_request
        ), 422

    conn = get_connection()
    name = get_scheme_hostname(url_from_request)
    existing_url_id = get_url_by_name(name, conn)

    if existing_url_id is not None:
        flash('Страница уже существует', 'info')
        close_connection(conn)
        return redirect(url_for('get_url_id', url_id=existing_url_id), 302)

    url_id = create_url(name, conn)

    if url_id is None:
        close_connection(conn)
        return render_template(
            'base.html',
            url_from_request=url_from_request
        ), 422

    conn.commit()
    flash('Страница успешно добавлена', 'success')
    close_connection(conn)
    return redirect(url_for('get_url_id', url_id=url_id), 302)


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    """Проверка статуса страницы."""
    conn = get_connection()
    url_data = get_url_by_id(url_id, conn)
    if not url_data:
        logging.error('Не удалось получить данные по ID')  # abort (404)
        close_connection(conn)
        return redirect(url_for('get_url_id', url_id=url_id))

    url_name = url_data['name']
    try:
        response = get_response(url_name)  # type: ignore
        if response is None:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('get_url_id', url_id=url_id))

        status_code = response.status_code
        if status_code != 200:
            flash('Произошла ошибка при проверке', 'danger')
            logging.warning('Код статуса не равен 200')
            return redirect(url_for('get_url_id', url_id=url_id))

        h1, title, description = get_tag_content(response)
        params = (
            url_id,
            status_code,
            h1,
            title,
            description,
            datetime.now().date()
        )
        if create_url_check(conn, params):
            conn.commit()
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('get_url_id', url_id=url_id))

    except requests.RequestException as e:
        flash('Произошла ошибка при проверке',
              'danger')
        logging.error('Ошибка при проверке страницы с ID %s: "%s"',
                      url_id, e)
        return redirect(url_for('get_url_id', url_id=url_id))
    finally:
        close_connection(conn)


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
