import sqlalchemy
import pandas as pd
from werkzeug.security import generate_password_hash
import getpass
import os

DB_USERNAME = os.environ.get("DB_USERNAME")

dbEngine = sqlalchemy.create_engine('sqlite:///database.db')


def create_user(username, password):
    df = pd.DataFrame({
        'id': [1],
        'username': [username],
        'password_hash': [generate_password_hash(password)]
    })
    df.to_sql('users', con=dbEngine, index=False, if_exists='replace')
    print("User Created:\n", df)


if __name__ == '__main__':
    pwd = getpass.getpass()
    create_user(DB_USERNAME, pwd)