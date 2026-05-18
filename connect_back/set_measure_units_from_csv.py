import os
import sys
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()
from common.catalogs.models import MeasureUnitModel


def main():
    try:
        file_name = sys.argv[1]
    except IndexError:
        print('Filename is missing! Example:\n\"python set_measure_units_from_csv.py file_name.csv\"')
        return
    try:
        with open(file_name, newline='') as csv_file:
            reader = csv.DictReader(
                csv_file,
                fieldnames=('code', 'name', 'name_plural', 'name_short'),
                restkey='',
                restval=''
            )
            for row in reader:
                print(
                    f"saving row\ncode={row['code']} name={row['name']} "
                    f"name_plural={row['name_plural']} name_short={row['name_short']}"
                )
                instance, created = MeasureUnitModel.objects.update_or_create(
                    code=row['code'],
                    defaults={
                        'name': row['name'],
                        'name_plural': row['name_plural'],
                        'name_short': row['name_short'],
                    }
                )
                if created:
                    print(f"instance created. id {instance.pk}\n")
                else:
                    print(f"instance updated. id {instance.pk}\n")
        print("Done.")
    except FileNotFoundError:
        print(f"File \"{file_name}\" not found.")
        return


if __name__ == "__main__":
    main()
