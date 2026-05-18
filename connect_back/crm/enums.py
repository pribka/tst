from enum import Enum


class OperationTypeEnum(Enum):
    draft = '10'
    offer = '20'
    price = '30'
    purchase = '40'
    to_return = '50'

    def __str__(self):
        return self.value
