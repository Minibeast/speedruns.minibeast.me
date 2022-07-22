from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import random

login = LoginManager()
db = SQLAlchemy()

class UserModel(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class GameModel(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    order_by = db.Column(db.Integer)
    name = db.Column(db.String())
    abbreviation = db.Column(db.String())
    use_game_time = db.Column(db.Boolean())
    show_on_home = db.Column(db.Boolean())


class CategoryModel(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    order_by = db.Column(db.Integer)
    held_game = db.Column(db.Integer)
    name = db.Column(db.String())
    abbreviation = db.Column(db.String())
    show_on_home = db.Column(db.Boolean())
    subcategory_filter = db.Column(db.Boolean())
    is_multiplayer = db.Column(db.Boolean())


class RunModel(db.Model):
    __tablename__ = 'runs'

    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.String())
    game = db.Column(db.Integer)
    category = db.Column(db.Integer)
    time = db.Column(db.Time)
    date = db.Column(db.Date)
    user = db.Column(db.Integer)
    players = db.Column(db.String())
    video = db.Column(db.String())
    subcategory = db.Column(db.String())
    platform = db.Column(db.String())
    demos = db.Column(db.String())
    splits = db.Column(db.String())

    def set_url_id(self):
        random_string = ''
        for _ in range(8):
            random_integer = random.randint(97, 97 + 26 - 1)
            flip_bit = random.randint(0, 1)
            random_integer = random_integer - 32 if flip_bit == 1 else random_integer

            random_string += chr(random_integer)

        if RunModel.query.filter_by(url_id=random_string).first() is None:
            self.url_id = random_string
        else:
            self.set_url_id()
            return


@login.user_loader
def load_user(id):
    return UserModel.query.get(int(id))
