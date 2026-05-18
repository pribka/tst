import os
import django
from math import ceil
from datetime import timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()
from bpms.tasks.models import TaskModel


def main():
    qs = TaskModel.objects.filter(
        is_active=True,
        task_type_id='logistic'
    ).exclude(status_id='completed').order_by('created_at')
    count = ceil(qs.count()/100)
    print(f"\nstart.")
    delta = timedelta(days=1)
    for each in range(count):
        tasks = qs[each*100:each*100+100]
        for task in tasks:
            date_start_plan = task.date_start_plan
            if date_start_plan:
                task.date_start_plan = date_start_plan + delta
            date_start_fact = task.date_start_fact
            if date_start_fact:
                task.date_start_fact = date_start_fact + delta
            task.save(update_fields=('date_start_plan', 'date_start_fact'))
            for delivery_point in task.task_delivery_points.all():
                delivery_date = delivery_point.delivery_date
                if delivery_date:
                    delivery_point.delivery_date = delivery_date + delta
            print(f"Task {task} updated.")
    print("Done.")


if __name__ == "__main__":
    main()
