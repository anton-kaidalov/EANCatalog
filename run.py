from flask import abort
from eve import Eve
from rq import Queue
from redis import Redis
from bulk_importer import BulkImporter
from validation import validate_task_status_transition

tasks_queue = Queue(connection=Redis(), default_timeout=3600) # one hour timeout for really long imports

def on_tasks_inserted(tasks):
    for task in tasks:
        sheet_id = task['sheet_id']
        task_id = str(task['_id'])
        print('Queueing the import task {} for sheet {}...'.format(task_id, sheet_id))
        importer = BulkImporter(task_id, sheet_id)
        tasks_queue.enqueue(importer.import_products_from_sheet)

def on_task_update(updates, original):
    old_status = original['status']
    new_status = updates['status']
    try:
        validate_task_status_transition(old_status, new_status)
    except Exception:
        abort(409, 'transition from {} to {} is not allowed'.format(old_status, new_status))

def on_task_delete(task):
    if task['status'] != 'Completed':
        abort(409, 'the task is not completed yet')

if __name__ == '__main__':
    app = Eve()
    app.on_inserted_bulk_import_tasks += on_tasks_inserted # post-hook, because we need the generated task id
    app.on_update_bulk_import_tasks += on_task_update # pre-hook, because we need to abort in some cases
    app.on_delete_item_bulk_import_tasks += on_task_delete # pre-hook, because we need to abort in some cases
    app.run()
