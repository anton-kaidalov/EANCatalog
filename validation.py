from stdnum import ean
from stdnum.exceptions import ValidationError
from stdnum.exceptions import InvalidLength

def validate_ean(field, value, error):
    try:
        validated_value = ean.validate(value)

        # stdnum allows 8/12/13 digits long EANs. For us, only EAN-13 works
        if len(validated_value) != 13:
            raise InvalidLength()
    except ValidationError as e:
        error(field, e.message)

def validate_task_status_transition(old_status, new_status):
    if old_status == new_status:
        return
    # only 4 transitions are allowed in our state machine
    if old_status == 'Not started':
        if new_status != 'In progress' and new_status != 'Cancelled':
            raise Exception()
    elif old_status == 'In progress':
        if new_status != 'Completed' and new_status != 'Cancelled':
            raise Exception()
    elif old_status == 'Completed':
        raise Exception()
    elif old_status == 'Cancelled':
        raise Exception()
    else:
        print('Unknown old status: {}'.format(old_status))
        raise Exception()
