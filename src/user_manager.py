from flask import Flask, session
from db import DatabaseAccess
from argon2 import PasswordHasher, exceptions
from enum import Enum
import secrets

class User:
    def __init__(self, user_id, name, is_superuser):
        self.user_id = user_id
        self.name = name
        self.is_superuser = is_superuser

class UserRegistrationResult(Enum):
        SUCCEEDED = 1
        USER_EXISTS_ERROR = 2
        UNKNOWN_ERROR = 3

class UserManager:
    def __init__(self, app: Flask, db_access: DatabaseAccess):
        self.db_access = db_access
        self.app = app

    def get_user(self, user_id):
        results = self.db_access.execute_sql_query(
            "SELECT * " \
            "FROM users " \
            "WHERE user_id = :userid",
            {"userid": user_id})
        
        if results is None or len(results) == 0:
            return None
        
        return User(results[0].user_id, results[0].name, results[0].is_superuser)
    
    def get_user_by_username(self, user_name):
        results = self.db_access.execute_sql_query(
            "SELECT * " \
            "FROM users " \
            "WHERE name = :username",
            {"username": user_name})
        
        if results is None or len(results) == 0:
            return None
        
        return User(results[0].user_id, results[0].name, results[0].is_superuser)
    
    def get_users(self, order_by_name = False):
        ordering = "user_id" if not order_by_name else "name"

        results = self.db_access.execute_sql_query(
            "SELECT * " \
            f"FROM users ORDER BY {ordering}",
            None)
        
        if results is None:
            return None
        
        users = []

        for result in results:
             users.append(User(result.user_id, result.name, result.is_superuser))
        
        return users

    def get_logged_user(self):
        with self.app.app_context():
            if "user_id" not in session:
                return None
            
            user_id = session["user_id"]
            user_name = session["user_name"]
            is_superuser = session["user_super"]

            return User(user_id, user_name, is_superuser)
        
    def logout_user(self):
        with self.app.app_context():
            session.clear()
        
    def logon_user(self, username, password):
        with self.app.app_context():
            ph = PasswordHasher()
            hash = ph.hash(password)

            results = self.db_access.execute_sql_query(
                "SELECT * " \
                "FROM users " \
                "WHERE name = :username",
                {"username": username})
            
            if len(results) == 0:
                return None
            
            hash = results[0].password
            
            try:
                if not ph.verify(hash, password):
                    return None
            except exceptions.VerifyMismatchError:
                return None
            
            user = User(results[0].user_id, results[0].name, results[0].is_superuser)

            session["user_id"] = user.user_id
            session["user_name"] = user.name
            session["user_super"] = user.is_superuser
            session["csrf_token"] = secrets.token_hex(16)
            
            return user
        
    def _user_exists(self, user_id):
        results = self.db_access.execute_sql_query(
            "SELECT COUNT(*) " \
            "FROM users " \
            "WHERE user_id = :userid",
            {"userid": user_id})
        
        if len(results) == 0 or results[0][0] == 0:
            return False

        return True
    
    def _username_exists(self, username):
        results = self.db_access.execute_sql_query(
            "SELECT COUNT(*) " \
            "FROM users " \
            "WHERE name = :username",
            {"username": username})
        
        if len(results) == 0 or results[0][0] == 0:
            return False

        return True
    
    def change_superuser_status(self, user_id, is_superuser):
        if not self._user_exists(user_id):
            return False

        result = self.db_access.execute_sql_command(
            "UPDATE users " \
            "SET is_superuser = :superuser " \
            "WHERE user_id = :userid",
            {
                "userid": user_id,
                "superuser": is_superuser
            })
        
        return result

    def register_user(self, username, password) -> UserRegistrationResult:
        ph = PasswordHasher()
        hash = ph.hash(password)

        result = self.db_access.execute_sql_command(
            "INSERT INTO users " \
            "(name, password)" \
            "VALUES (:name, :password)",
            {
                "name": username,
                "password": hash
            })
        
        if not result:
            if self._username_exists(username):
                return UserRegistrationResult.USER_EXISTS_ERROR

            return UserRegistrationResult.UNKNOWN_ERROR

        return UserRegistrationResult.SUCCEEDED
