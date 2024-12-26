import logging
import os

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

from page_analyzer.database import (
    check_existing_url,
    close_connection,
    create_new_url,
    create_url_check,
    get_all_urls,
    get_connection,
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
    conn = get_connection()
    urls = get_all_urls(conn)
    close_connection(conn)
    return render_template('urls.html', urls=urls)


@app.get('/urls/<int:url_id>')
def get_url_id(url_id: int):
    """Возвращает страницу с полной информацией."""
    conn = get_connection()
    url_data = get_one_url(url_id, conn)
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
def add_url():
    """Добавление новой страницы."""
    url_from_request = request.form.get('url', '')

    if not validate(url_from_request):
        flash('Некорректный URL', 'danger')
        return render_template(
            'base.html',
            url_from_request=url_from_request
        ), 422

    conn = get_connection()
    existing_url_id = check_existing_url(url_from_request, conn)

    if existing_url_id is not None:
        flash('Страница уже существует', 'info')
        return redirect(url_for('get_url_id', url_id=existing_url_id), 302)

    url_id = create_new_url(url_from_request, conn)

    conn.commit()
    close_connection(conn)

    if url_id is None:
        return render_template(
            'base.html',
            url_from_request=url_from_request
        ), 422

    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('get_url_id', url_id=url_id), 302)


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    """Проверка статуса страницы."""
    result = create_url_check(url_id)
    if result is None:
        flash('Произошла ошибка при проверке', 'danger')
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
    app.run()
