from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import exc
from os import getenv

class SqlReturnValuePlaceholder:
    def __init__(self):
        pass

class DatabaseAccess:
    def __init__(self, app):
        app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
        self.db = SQLAlchemy(app)
        self.app = app

    def execute_sql_query(self, sql, sql_params = None):
        with self.app.app_context():
            try:
                result = self.db.session.execute(text(sql), sql_params)
                data = result.all()

                return data
            except Exception as error:
                print("Exception on SQL query:", error)
                return None

    def execute_sql_command(self, sql, sql_params):
        with self.app.app_context():
            try:
                self.db.session.execute(text(sql), sql_params)
                self.db.session.commit()
            except Exception as error:
                print("Exception on SQL command execution:", error)
                return False

            return True
    
    def execute_sql_command_with_return(self, sql, sql_params):
        with self.app.app_context():
            try:
                result = self.db.session.execute(text(sql), sql_params)
                self.db.session.commit()

                return result.first()
            except Exception as error:
                print("Exception on SQL command execution:", error)

            return None

    def execute_sql_commands_in_transaction(self, sql_statements):
        with self.app.app_context():
            try:
                returned_value = None

                for sql, sql_params in sql_statements:
                    if returned_value is not None:
                        # Inject previously returned value instead of special marker in sql_params
                        for key in sql_params.keys():
                            if isinstance(sql_params[key], SqlReturnValuePlaceholder):
                                sql_params[key] = returned_value

                    result = self.db.session.execute(text(sql), sql_params)

                    if result.returns_rows:
                        returned = result.first()
                        returned_value = returned[0] if returned is not None and len(returned) > 0 else None
                    else:
                        returned_value = None

                self.db.session.commit()
            except Exception as error:
                print("Exception on SQL commands execution:", error)
                return False

            return True