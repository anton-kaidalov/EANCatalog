from flask import abort
from eve import Eve
from eve.methods.post import post_internal
from bulk_import import get_products_from_sheet

def on_tasks_insert(documents):
    # Eve ensures that documents is a list with basic validation passed
    if len(documents) != 1:
        abort(400, 'You can only submit one task at a time.')
    sheet_id = documents[0]['sheet_id']
    try:
        for product in get_products_from_sheet(sheet_id):
            print("Importing {}... ".format(product), end='')
            result = post_internal('products', product)
            print(result[3]) # HTTP status code
    except Exception as e:
        abort(400, 'Import from Google Sheets failed. Check that the sheet exists, has access by link enabled and has proper content.')

if __name__ == '__main__':
    app = Eve()
    app.on_insert_bulk_import_tasks += on_tasks_insert
    app.run()
