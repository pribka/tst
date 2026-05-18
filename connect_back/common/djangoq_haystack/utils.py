from django.core.exceptions import ImproperlyConfigured
from django.apps import apps

from haystack import connections, connection_router
from haystack.exceptions import NotHandled


def run_task(action, identifier):
    object_path, pk = split_identifier(identifier)
    if object_path is None or pk is None:
        msg = "Couldn't handle object with identifier %s" % identifier
        raise ValueError(msg)
    model_class = get_model_class(object_path)
    for current_index, using in get_indexes(model_class):
        if action == 'delete':
            current_index.remove_object(identifier, using=using)
        elif action == 'update':
            instance = model_class._default_manager.get(pk=pk)
            current_index.update_object(instance, using=using)
        else:
            return  # TODO обработка исключения


def split_identifier(identifier):
    bits = identifier.split('.')
    if len(bits) < 2:
        return (None, None)
    pk = bits[-1]
    object_path = '.'.join(bits[:-1])
    return (object_path, pk)


def get_model_class(object_path):
    bits = object_path.split('.')
    app_name = '.'.join(bits[:-1])
    classname = bits[-1]
    model_class = apps.get_model(app_name, classname)

    if model_class is None:
        raise ImproperlyConfigured("Could not load model '%s'." % object_path)
    return model_class


def get_indexes(model_class):
    try:
        using_backends = connection_router.for_write(**{'models': [model_class]})
        for using in using_backends:
            index_holder = connections[using].get_unified_index()
            yield index_holder.get_index(model_class), using
    except NotHandled:
        raise ImproperlyConfigured("Couldn't find a SearchIndex for %s." %
                                   model_class)








