#!/usr/bin/env python
import dancify
import config

app = dancify.create_app(config)

# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
