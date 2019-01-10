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
