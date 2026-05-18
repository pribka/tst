import os
import sys
import argparse

# Добавим корень проекта в sys.path, чтобы Python "видел" settings и приложения
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, BASE_DIR)

# Установим переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')  # Замените 'bkz3' на имя вашего проекта

# Инициализация Django
import django
django.setup()

from django.apps import apps

def collect_all_models():
    """
    Собирает и возвращает отсортированный список всех моделей Django в формате 'app_label.ModelName'.
    Запуск в терминале: python reports/utils/collect_models.py
    """
    model_paths = []
    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model.__name__
        model_paths.append(f"{app_label}.{model_name}")
    return sorted(model_paths)

if __name__ == "__main__":
    models_list = collect_all_models()
    print("REPORTS_UNIVERSAL_MODELS = [")
    for model_path in models_list:
        print(f"'{model_path}',")
    print("]")