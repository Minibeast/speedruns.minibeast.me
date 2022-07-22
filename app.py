from flask import Flask, render_template, request, redirect
from flask_login import current_user, login_user, logout_user
from models import *
import private

import management
import feeds
import routes

app = Flask(__name__)
app.secret_key = private.SECRET

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
    def check_value(value : str) -> str:
        if value is None:
            return ""
        return value
    return dict(check_value=check_value)


@app.before_first_request
def create_all():
    db.create_all()


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    
    if request.method == 'POST':
        username = private.USERNAME
        user = UserModel.query.filter_by(username=username).first()
        if user is not None and user.check_password(request.form['pwd']):
            login_user(user)
            if 'next' in request.args:
                return redirect(request.args['next'])
            else:
                return redirect("/")

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")
