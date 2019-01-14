from googleapiclient.discovery import build
import os

RANGE = 'A1:E'
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

service = build('sheets', 'v4', developerKey=GOOGLE_API_KEY)
sheets = service.spreadsheets()

def get_products_from_sheet(sheet_id):
    print("Importing products from sheet {}...".format(sheet_id))
    values = sheets.values().get(spreadsheetId=sheet_id, range=RANGE).execute()['values']
    headers = values[0]
    products = []
    for fields in values[1:]:
        product = dict(zip(headers, fields))
        products.append(product)
    return products
