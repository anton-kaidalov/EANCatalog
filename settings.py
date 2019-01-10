from validation import validate_ean

RESOURCE_METHODS = ['GET', 'POST']
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']

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

for k in products_schema:
    products_schema[k]['required'] = True

DOMAIN = {
    'products': {
        'schema': products_schema
    }
}
