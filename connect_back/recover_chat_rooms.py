import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()
from bpms.chat.utils import recover_chat_rooms


def main():
    recover_chat_rooms()
    return


if __name__ == '__main__':
    main()
