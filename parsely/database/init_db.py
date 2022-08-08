from flask import Flask
from database.db_utils import registerDB, resetDB

app = Flask(__name__)
registerDB(app)
resetDB(app)
