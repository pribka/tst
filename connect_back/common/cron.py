import os
import time

from bkz3.settings import ZIPFILES_ROOT, ZIPFILES_EXPIRE


def clear_zipfiles_root():
    """
    Удаляет протухшие файлы в каталоге со сгенерированными zip-архивами.
    Используется в запланированных задачах.
    """
    now = time.time()
    for file in os.listdir(ZIPFILES_ROOT):
        if now - os.path.getmtime(os.path.join(ZIPFILES_ROOT, file)) > ZIPFILES_EXPIRE:
            try:
                os.remove(os.path.join(ZIPFILES_ROOT, file))
            except OSError:
                pass


