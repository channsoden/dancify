#!/usr/bin/env python
from flask import Flask
from data import authorize_sheets

app = Flask(__name__)
 
@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/class_data')
def class_data():
    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    SAMPLE_RANGE_NAME = 'Class Data!A2:E'

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    lines = []
    if not values:
        lines.append('No data found.')
    else:
        lines.append('Name, Major:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            lines.append('{}, {}'.format(row[0], row[4]))

    html = '<br />'.join(lines)
    return html

@app.route('/playlist/<ID>')
def view_playlist(ID):
    return 'Playlist ID: {}'.format(ID)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']



if __name__ == '__main__':
    service = None
    authorize_sheets()
    app.run(debug=True, host='0.0.0.0')
