from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user
from models import *
import os

import management
import feeds
import routes

EXTERNAL_CSS = os.environ.get("EXTERNAL_CSS")
SITE_NAME = os.environ.get("SITE_NAME")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_SECRET = os.environ.get("DB_SECRET")

app = Flask(__name__)
app.secret_key = DB_SECRET

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(management.management, url_prefix='/actions')
app.register_blueprint(feeds.feeds, url_prefix='/')
app.register_blueprint(routes.routes, url_prefix='/')

db.init_app(app)
login.init_app(app)
login.login_view = 'login'


@app.context_processor
def utility_processor():
    external_css = EXTERNAL_CSS if EXTERNAL_CSS else ""
    site_name = SITE_NAME if SITE_NAME else "Speedruns"
    def check_value(value : str) -> str:
        if value is None:
            return ""
        return value
    return dict(check_value=check_value, external_css=external_css, site_name=site_name)


@app.before_first_request
def create_all():
    db.create_all()


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.load_runs"))
    
    if request.method == 'POST':
        username = DB_USERNAME
        user = UserModel.query.filter_by(username=username).first()
        if user is not None and user.check_password(request.form['pwd']):
            login_user(user)
            if 'next' in request.args:
                return redirect(request.args['next'])
            else:
                return redirect(url_for("routes.load_runs"))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("routes.load_runs"))
