from validation import validate_ean

RESOURCE_METHODS = ['GET', 'POST']
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']

HATEOAS = False

products_schema = {
    'name': {
        'type': 'string'
    },
    'brand': {
        'type': 'string'
    },
    'category': {
        'type': 'string'
    },
    'price': {
        'type': 'float'
    },
    'ean': {
        'type': 'string',
        'validator': validate_ean
    }
}

bulk_import_tasks_schema = {
    'sheet_id': {
        'type': 'string',
        'required': True
    },
    'status' : {
        'type': 'string',
        'required': True,
        'allowed': ['Not started', 'In progress', 'Completed', 'Cancelled'],
        'default': 'Not started'
    }
}

for k in products_schema:
    products_schema[k]['required'] = True

DOMAIN = {
    'products': {
        'schema': products_schema
    },
    'bulk_import_tasks': {
        'schema': bulk_import_tasks_schema
    }
}
