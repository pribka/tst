# action_registry.py

action_registry = {}

def register_action(form_name, action_name):
    def decorator(func):
        action_registry.setdefault(form_name, {})[action_name] = func
        return func
    return decorator

def get_registered_action(form_name, action_name):
    try:
        return action_registry[form_name][action_name]
    except KeyError:
        return None
