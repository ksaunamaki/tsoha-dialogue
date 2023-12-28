# Configures database connection and site settings
import os
from db import DatabaseAccess
from user_manager import UserManager
from site_config import SiteConfiguration
from flask import Flask

def get_yes_no_answer(prompt, default):
    answer = input(prompt)

    if answer not in ['y','Y','n','N']:
        return default
    
    return answer.lower()

def setup_database_connection():
    server = input("Enter Postgres database server address (or enter for local): ")
    database = input("Enter database name to use (or enter for default 'dialogue'): ")

    if database == "":
        database = "dialogue"

    credentials = ""

    if get_yes_no_answer("Do you want to specify explicit credentials " + 
                         "to connect to database (N/y)? ", 'n') == 'y':
        user_name = input("Enter Postgres username to use: ")

        if user_name == "":
            print("Assuming no explicit credentials are needed afterall!")
        else:
            password = input("Enter Postgres user's password: ")

            if user_name == "":
                print("Assuming no explicit credentials are needed afterall!")
            else:
                credentials = f"{user_name}:{password}@"

                if server == "":
                    server = "localhost"

    try:
        with open("src/.env", "w") as env_file:
            env_file.write(f"DATABASE_URL=postgresql://{credentials}{server}/{database}\n")
    except:
        print("Cannot write .env file with database connection, please create manually!")
        return False
    
    return True

def get_database_connection():
    try:
        with open("src/.env") as env_file:
            for row in env_file:
                if row.startswith("DATABASE_URL"):
                    parts = row.split("=")
                    if len(parts) >= 2:
                        return parts[1].strip('\n')
    except:
        print("Cannot read .env file for database connection!")
    
    return None

def get_database_tables():
    tables = []

    try:
        with open("src/tables.sql") as tables_file:
            for row in tables_file:
                command = row.strip('\n')

                if command == "":
                    continue

                tables.append(command)
    except:
        print("Cannot read tables.sql file for database table information!")
        return None
    
    return tables

def modify_user(user_manager, user_name):
    user = user_manager.get_user_by_username(user_name)

    if user is None:
        print("User by given username not found!")
        return
    
    if user.is_superuser:
        if get_yes_no_answer("User is currently a superuser, " + 
                                "do you want to change it to normal one (N/y)? ", 'n') == 'n':
            return
        
        if not user_manager.change_superuser_status(user.user_id, False):
            print(f"User {user.name}'s superuser status could NOT be changed!")
            
        return
    
    if get_yes_no_answer("User is currently normal user, " + 
                                "do you want to grant superuser status for it (N/y)? ", 'n') == 'n':
            return
    
    if not user_manager.change_superuser_status(user.user_id, True):
            print(f"User {user.name}'s superuser status could NOT be changed!")


def modify_site_superusers(user_manager):
    if get_yes_no_answer("Do you want to change site superusers (N/y)? ", 'n') == 'n':
        return
    
    answer = ""

    while answer != "x":
        answer = input("Enter username to change superuser status for, ? to list users or x to exit: ")

        if answer == "x":
            continue
        elif answer == "?":
            users = user_manager.get_users(True)

            if users is None:
                print("Error while enumerating current users from database!")
                return
            
            for user in users:
                print(f"{user.name} (ID: {user.user_id}) - is superuser: {user.is_superuser}")
        elif answer != "":
            modify_user(user_manager, answer)


def modify_site_parameters(site_configuration):
    if get_yes_no_answer("Do you want to change site name (N/y)? ", 'n') == 'y':
        site_name = input("Enter new name for site: ")

        if site_name != "":
            if not site_configuration.set_configuration_value('sitename', site_name):
                print("Site name update failed!")
                return

def setup_database(db):
    database_uri = get_database_connection()

    if database_uri is None:
        return False

    db = DatabaseAccess(Flask(__name__), database_uri)

    database_tables = get_database_tables()

    if database_tables is None:
        return False
    
    # Check that database exists and is accessible
    results = db.execute_sql_command_with_return("SELECT * FROM information_schema.tables", None)

    if results is None:
        print()
        print("Unable to connect to specified Postgres server or database; please check connection in .env file" \
              " and that specified database is created on the server!")
        return False
    
    # Check that tables exists
    for table_creation in database_tables:
        if not table_creation.startswith('CREATE TABLE '):
            continue

        # Take table name from third word in SQL script
        parts = table_creation.split(' ')

        if len(parts) < 3:
            continue

        table = parts[2]

        results = db.execute_sql_command_with_return("SELECT EXISTS (" \
                                "SELECT 1 FROM information_schema.tables " \
                                "WHERE table_name = :table" \
                                ") AS table_exists;",
                                {"table": table})
        
        if results is None or len(results) == 0:
            print("Unable to connect to specified Postgres server or database; please check connection in .env file" \
              " and that specified database is created on the server!")
            return False
    
        if not results[0]:
            print(f"Creating new table '{table}' ", end="")
            results = db.execute_sql_command(table_creation, None)

            if not results:
                print("failed, please check database!")
                return False
            
            print("ok")

    return True

def site_configure(site_configuration, user_manager):
    # Allow changing site parameters
    modify_site_parameters(site_configuration)

    # Allow changing site superusers (i.e. admins)
    modify_site_superusers(user_manager)

if __name__ == "__main__":
    if not os.path.exists('src/.env') or \
        get_yes_no_answer("Do you want to change database connection (N/y)? ", 'n') == 'y':

        if not setup_database_connection():
            exit()

    database_uri = get_database_connection()

    if database_uri is None:
        print("Unable to get database connection to configure site!")
        exit()

    app = Flask(__name__)
    db = DatabaseAccess(app, database_uri)
    site_configuration = SiteConfiguration(app, db)
    user_manager = UserManager(app, db)

    if not setup_database(db):
        exit()

    site_configure(site_configuration, user_manager)
