# search/services.py
from typing import Optional, Dict, Any
from django.http import HttpRequest
import importlib

def universal_search(model: str, search: str):
    """
    Универсальная точка входа для поиска по разным моделям.
    Параметры:
      - model: "app_label.ModelName" (например, "users.ProfileModel")
      - search: строка поиска
      - page, page_size: пагинация (используется только в ES)
      - request: игнорируется (видимость не учитывается на этом шаге)

    Возвращает список словарей с id и score (без учета видимости)
    
    Соглашение: функция поиска должна называться search_{app_label}_{model_name.lower()}
    и находиться в файле search/searchers/{app_label}_{model_name.lower()}.py
    """
    if not model:
        return {"error": "Param 'model' is required."}
    
    try:
        app_label, model_name = model.split('.', 1)
        function_name = f"search_{app_label}_{model_name.lower()}"
        module_name = f"{app_label}_{model_name.lower()}"
        module = importlib.import_module(f"es_search.searchers.{module_name}")
        searcher = getattr(module, function_name)
        return searcher(search=search)
    except (ValueError, ImportError, AttributeError) as e:
        return {"error": f"Unknown model '{model}' or searcher not found: {str(e)}"}
