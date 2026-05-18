def validate_quantity(value):
    try:
        from bkz3.settings import GLOBAL_FRONT_SETTINGS
        cartDecimalCount = GLOBAL_FRONT_SETTINGS.get('order_setting').get('cartDecimalCount')
    except:
        cartDecimalCount = False
    
    if cartDecimalCount:
        return value
    else:
        value = round(value)
        if value < 1:
            value = 1
        return round(value)
