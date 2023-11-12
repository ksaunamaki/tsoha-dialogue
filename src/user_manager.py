from flask import Flask
from db import DatabaseAccess
from flask import session

class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

class UserManager:
    def __init__(self, app: Flask, db_access: DatabaseAccess):
        self.db_access = db_access
        self.app = app

    def get_logged_user(self):
        with self.app.app_context():
            if "user_id" not in session:
                return None
            
            user_id = session["user_id"]

            return User(user_id, "")