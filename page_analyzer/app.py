import os
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    # request,
    # redirect,
    # url_for,
)


load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    """Return the main page."""
    return render_template('index.html')


@app.route('/urls')
def urls():
    return 'URLS'


if __name__ == '__main__':
    app.run()
