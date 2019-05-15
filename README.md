# Dancify

Dancify is a web app that lets you visualize, filter, and tag your Spotify music collections.

## Data Collection

Dancify keeps no Spotify data. User's authorization tokens are stored as cookies with the user and retrieved upon requests. Dancify only stores user tags and preferences, which are associated with spotify user IDs.

## Implementation

Dancify is built using the [Flask](http://flask.pocoo.org/) web framework for Python. The vizualization elements are implemented using [Dash](https://plot.ly/products/dash/), the Flask-based web app for Plotly. Dancify uses a Google Cloud SQL database accessed through [SQLAlchemy](https://docs.sqlalchemy.org/en/13/) and the [Spotipy](https://spotipy.readthedocs.io/en/latest/) library for the Spotify API.
