import os

# The secret key is used by Flask to encrypt session cookies.
SECRET_KEY = 'DEV'#os.getenv('DANCIFY_SECRET_KEY')

# Dancify client id and client secret from Spotify.
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Google Cloud Project ID.
PROJECT_ID = 'dancifydev'

# When deployed to App Engine, the `GAE_ENV` environment variable will be
# set to `standard`
if os.environ.get('GAE_ENV') == 'standard':
    SERVER_NAME = 'dancifydev.appspot.com'
else:
    SERVER_NAME = 'localhost:5000'

# CloudSQL configuration
# Replace the following values the respective values of your Cloud SQL
# instance.
CLOUDSQL_USER = os.getenv('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.getenv('CLOUDSQL_PASSWORD')
CLOUDSQL_DATABASE = os.getenv('CLOUDSQL_DATABASE')
# Set this value to the Cloud SQL connection name, e.g.
#   "project:region:cloudsql-instance".
# You must also update the value in app.yaml.
CLOUDSQL_CONNECTION_NAME = os.getenv('CLOUDSQL_CONNECTION_NAME')
DB_POOL_SIZE = os.getenv('DB_POOL_SIZE')

# The CloudSQL proxy is used locally to connect to the cloudsql instance.
# To start the proxy, use:
#
#   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
#
# Port 3306 is the standard MySQL port. If you need to use a different port,
# change the 3306 to a different port number and edit dancify/db.py.
