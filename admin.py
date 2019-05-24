import sys

from flask import Flask
from sqlalchemy.sql import select

from dancify import db
import config

def create_app(config, debug=True, testing=True):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)

    app.debug = True
    app.testing = True

    db.init_engine(app)

    @app.route('/')
    def index():
        return "Admin tools"
    
    return app

def clear_preferences_db():
    confirm = input('Type CONFIRM to clear the preferences database.')
    if confirm == 'CONFIRM':
        conn = get_db()
        conn.execute(db.preferences_table.delete())
        conn.close()
        return 'preferences_table cleared'
    else:
        return 'preferences_table not cleared'

def show_preferences_db():
    conn = db.engine.connect()
    message = ['Preferences DB is:']
    result = conn.execute(select([db.preferences_table]))
    for row in result:
        message.append( '\t'.join(row) )
        
    conn.close()
    return '\n'.join(message)

if __name__ == '__main__':
    app = create_app(config)
    
    commands = sys.argv[1:]
    for com in commands:
        print( eval(com+'()') )
        print()
