#!/usr/bin/env python
import os

from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from flask import g
from flask.cli import with_appcontext

engine = None

metadata = MetaData()
tag_table = Table('tags', metadata,
                  Column('user_id', String(40), primary_key=True),
                  Column('song_id', String(22), primary_key=True),
                  Column('tag', String(60), primary_key=True) )

preferences_table = Table('preferences', metadata,
                          Column('user_id', String(40), primary_key=True),
                          Column('collections', String(22), primary_key=False) )

def init_engine(app):
    db_user = app.config['CLOUDSQL_USER']
    db_password = app.config['CLOUDSQL_PASSWORD']
    db_connection_name = app.config['CLOUDSQL_CONNECTION_NAME']
    db_name = app.config['CLOUDSQL_DATABASE']
    pool_size = int(app.config['DB_POOL_SIZE'])

    # When deployed to App Engine, the `GAE_ENV` environment variable will be
    # set to `standard`
    if os.environ.get('GAE_ENV') == 'standard':
        # If deployed, use the local socket interface for accessing Cloud SQL
        unix_socket = '/cloudsql/{}'.format(db_connection_name)
        engine_url = 'mysql+pymysql://{}:{}@/{}?unix_socket={}'.format(
            db_user, db_password, db_name, unix_socket)
    else:
        # If running locally, use the TCP connections instead
        # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
        # so that your application can use 127.0.0.1:3306 to connect to your
        # Cloud SQL instance
        host = '127.0.0.1'
        engine_url = 'mysql+pymysql://{}:{}@{}/{}'.format(
            db_user, db_password, host, db_name)

    global engine
    engine = create_engine(engine_url, pool_size=pool_size)
    
    # Create data tables if not already existant.
    metadata.create_all(engine)

    # Automatically return connections to the pool when the request ends
    app.teardown_appcontext(close_db)

def get_db():
    if 'db' not in g:
        g.db = engine.connect()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


