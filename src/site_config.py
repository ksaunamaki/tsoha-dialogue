from flask import Flask
from db import DatabaseAccess
import secrets

class SiteConfiguration:
    _site_name = ""

    def __init__(self, app: Flask, db_access: DatabaseAccess, init = True):
        self.db_access = db_access

        if init:
            self.initialize_site_params(app)

    @property
    def site_name(self):
        return self._site_name
    
    def get_configuration_value(self, value_name):
        results = self.db_access.execute_sql_query("SELECT setting_value FROM site_settings WHERE setting_id = :name",
                                                    {"name":value_name})
        
        if results is None or len(results) == 0:
            return None
        
        return results[0].setting_value
    
    def set_configuration_value(self, value_name, value_data):
        results = self.db_access.execute_sql_command("INSERT INTO site_settings (setting_id, setting_value) " \
                                                         "VALUES (:id, :value) ON CONFLICT (setting_id) DO " \
                                                         "UPDATE SET setting_value = :value",
                                                        {
                                                            "id": value_name,
                                                            "value": value_data
                                                        })
        
        if results is None or not results:
            return False
        
        return True

    def initialize_secret(self, app: Flask):
        # Get secret key for session cookie
        secret_key = self.get_configuration_value("secretkey") or ""
        
        if secret_key == "":
            # None found from DB, generate new one

            print("Creating new secret_key for site")
            secret_key = secrets.token_hex(16)
            if not self.db_access.execute_sql_command("INSERT INTO site_settings VALUES (:secretkey, :data)",
                                                 { "secretkey":"secretkey", "data":secret_key }):
                print("ERROR: Cannot store generated Flask secret_key to site settings!")

        app.secret_key = secret_key
    
    def initialize_branding(self):
        self._site_name = self.get_configuration_value("sitename") or "Default Dialogue site"

    def initialize_site_params(self, app: Flask):
        self.initialize_secret(app)
        self.initialize_branding()
