from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import exc
from os import getenv

class DatabaseAccess:
    def __init__(self, app):
        app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
        self.db = SQLAlchemy(app)
        self.app = app

    def execute_sql_select(self, sql, sql_params = None):
        with self.app.app_context():
            try:
                result = self.db.session.execute(text(sql), sql_params)
                data = result.fetchall()

                return data
            except Exception as error:
                print("Exception on SQL select:", error)
                return None

    def execute_sql_insert(self, sql, sql_params):
        with self.app.app_context():
            try:
                self.db.session.execute(text(sql), sql_params)
                self.db.session.commit()
            except Exception as error:
                print("Exception on SQL insert:", error)
                return False

            return True
        
