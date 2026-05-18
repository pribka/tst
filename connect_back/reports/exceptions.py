from rest_framework.exceptions import APIException


class InvalidTablePartError(APIException):
    status_code = 400
    default_detail = 'Invalid table part.'
    default_code = 'invalid_table_part'


class InvalidTablePartOperation(APIException):
    status_code = 400
    default_detail = 'Invalid table part operation.'
    default_code = 'invalid_table_part_operation'