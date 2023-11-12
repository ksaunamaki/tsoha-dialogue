from flask import Flask
from db import DatabaseAccess
from site_config import SiteConfiguration
from topic_manager import TopicManager
from user_manager import UserManager

app = Flask(__name__)

db_access = DatabaseAccess(app)
site_config = SiteConfiguration(app, db_access)
topic_manager = TopicManager(db_access)
user_manager = UserManager(app, db_access)

import routes
