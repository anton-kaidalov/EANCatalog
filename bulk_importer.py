from googleapiclient.discovery import build
import os
import requests
import time

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY'] # obtained from Google dev console
WORKSHEET_INDEX = 0 # inside the Google Sheet
RANGE_TEMPLATE = '{}!A{}:E{}'
HEADERS = ['name', 'brand', 'category', 'price', 'ean']

PRODUCTS_URL = 'http://localhost:5000/products'
TASK_URL_TEMPLATE = 'http://localhost:5000/bulk_import_tasks/{}'

# two empiric dev-only values. Balancing performance and avoiding service denial because of Google Sheets quotas on free account
# production solution should be configured with proper quota values from Google dev console
IMPORT_BUFFER_SIZE = 5000
SLOWDOWN_SECONDS = 2

service = build('sheets', 'v4', developerKey=GOOGLE_API_KEY)
sheets = service.spreadsheets()

class BulkImporter():
    def __init__(self, task_id, sheet_id):
        self.task_id = task_id
        self.sheet_id = sheet_id

    def _refresh_task_params(self):
        print('Getting task {}...'.format(self.task_id))
        response = requests.get(TASK_URL_TEMPLATE.format(self.task_id))
        if response.status_code != 200:
            # no way of continuing
            raise Exception('Could not get the task: {} {}'.format(response.status_code, response.text))
        self.task_status = response.json()['status']
        self.task_etag = response.json()['_etag']

    def _update_task_status(self, status):
        print('Transitioning task {} to {}...'.format(self.task_id, status))
        response = requests.patch(TASK_URL_TEMPLATE.format(self.task_id), json={'status': status}, headers={'If-Match': self.task_etag})
        if response.status_code != 200:
            # no way of continuing
            raise Exception('Task status update failed: {} {}'.format(response.status_code, response.text))
        self.task_status = status
        self.task_etag = response.json()['_etag']

    def _refresh_sheet_params(self):
        print('Getting Google Sheet parameters...')
        response = sheets.get(spreadsheetId=self.sheet_id, fields='sheets(properties(index,sheetId,title,gridProperties))').execute()
        self.sheet_row_count = response['sheets'][WORKSHEET_INDEX]['properties']['gridProperties']['rowCount'] # approximate, includes empty rows
        self.worksheet_title = response['sheets'][WORKSHEET_INDEX]['properties']['title']
        print('Approximate row count: {}'.format(self.sheet_row_count))
        print('Worksheet title: {}'.format(self.worksheet_title))

    def _get_rows_in_range(self, row_start, row_end):
        range = RANGE_TEMPLATE.format(self.worksheet_title, row_start, row_end-1) # without the last one
        print('Obtaining data in the range {}...'.format(range))
        response = sheets.values().get(spreadsheetId=self.sheet_id, range=range, valueRenderOption='UNFORMATTED_VALUE').execute()
        if 'values' in response:
            print('Obtained rows: {}'.format(len(response['values'])))
            return response['values']
        print('Obtained 0 rows.')
        return None

    def _create_products(self):
        print('Number of products to create: {}. Creating...'.format(len(self.products)))
        response = requests.post(PRODUCTS_URL, json=self.products)
        print('Resulting HTTP status: {}'.format(response.status_code))
        if response.status_code != 201:
            # it's likely that some products failed the validation, and Eve discarded the whole bunch
            # let's try once more with the valid ones
            results = response.json()['_items']
            invalid_products = []
            valid_products = []
            for i in range(0, len(self.products)):
                if results[i]['_status'] == 'OK':
                    valid_products.append(self.products[i])
                else:
                    invalid_products.append(self.products[i])
            if not valid_products:
                # the whole bunch was invalid
                return
            print(
                'Some of the products ({}) failed to pass validation. Trying to resubmit just the successful ones ({})...'
                .format(len(invalid_products), len(valid_products))
            )
            response = requests.post(PRODUCTS_URL, json=valid_products)
            print('Resulting HTTP status: {}'.format(response.status_code))
            if response.status_code != 201:
                # not raising anything, continuing
                print('Resubmission of the successful products also failed: {} {}'.format(response.status_code, response.json()))

    def import_products_from_sheet(self):
        print('Processing bulk import task {} with Google Sheet {}...'.format(self.task_id, self.sheet_id))
        self._refresh_task_params()
        if self.task_status != 'Not started':
            print('Task has status {}, stopping'.format(self.task_status))
            return
        self._update_task_status('In progress')
        self._refresh_sheet_params()
        row_start = 2 # skipping headers row
        while row_start <= self.sheet_row_count:
            time.sleep(SLOWDOWN_SECONDS)
            self._refresh_task_params() # it may have been cancelled
            if self.task_status == 'Cancelled':
                print('Task is cancelled, stopping')
                return
            row_end = row_start + IMPORT_BUFFER_SIZE
            if row_end > self.sheet_row_count+1:
                row_end = self.sheet_row_count+1
            rows = self._get_rows_in_range(row_start, row_end)
            if rows:
                # compose a list of product dicts using headers, excluding rows with empty fields
                self.products = [dict(zip(HEADERS, fields)) for fields in rows if any(f for f in fields)]
                self._create_products()
            row_start = row_end # next buffer
        self._update_task_status('Completed')
