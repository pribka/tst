from datetime import datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta
from rest_framework import exceptions as drf_exceptions

from bkz3.settings import TIME_ZONE

from . import models as wl_models


def set_default_work_days():
    return {
        'monday': True,
        'tuesday': True,
        'wednesday': True,
        'thursday': True,
        'friday': True,
        'saturday': False,
        'sunday': False
    }


def calc_duration(start, end):
    today = datetime.today()
    start = datetime.combine(today, start)
    end = datetime.combine(today, end)
    if start > end:
        duration = end + timedelta(days=1) - start
    else:
        duration = end - start
    return duration


def add_time(time_1, time_2):
    today = datetime.today()
    datetime_1 = datetime.combine(today, time_1)
    datetime_2 = datetime.combine(today, time_2)
    delta = datetime_2 - datetime(1900, 1, 1)
    return (datetime_1 + delta).time()


def convert_timedelta_to_time(timedelta):
    total_seconds = int(timedelta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=hours, minute=minutes, second=seconds)


def convert_time_to_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


def get_correct_timezone_date(date, timezone):
    date = str(date)
    date = datetime.fromisoformat(date)
    timezone = pytz.timezone(timezone)
    date = date.astimezone(timezone)
    return date


def get_total_duration(tasks, schedule, date):
    amount = time(0, 0, 0)
    midnight = datetime.min.time()
    for task in tasks:
        try:
            task_dur = wl_models.TaskDurationModel.objects.get(task=task)
        except wl_models.TaskDurationModel.DoesNotExist:
            task_dur = wl_models.TaskDurationModel.objects.create(
                task=task, is_distributed=False
            )
        if task_dur.is_distributed:
            try:
                hours = next((
                    duration['hours']
                    for duration in task_dur.durations
                    if duration['date'] == str(date)
                ), None)
            except drf_exceptions.ValidationError:
                raise drf_exceptions.ValidationError()
            duration = datetime.strptime(f'{hours}:00:00', '%H:%M:%S').time()
            amount = add_time(amount, duration)
        else:
            start_plan = task.date_start_plan
            dead_line = task.dead_line
            if dead_line.date() == start_plan.date():
                duration = dead_line - start_plan
                duration = convert_timedelta_to_time(duration)
                amount = add_time(amount, duration)
            else:
                if start_plan.date() == date:
                    start_plan = get_correct_timezone_date(
                        start_plan, TIME_ZONE
                    )
                    duration = calc_duration(
                        start_plan.time(),
                        midnight if start_plan.time() > schedule.end_hour
                        else schedule.end_hour
                    )
                    amount = add_time(
                        amount, convert_timedelta_to_time(duration)
                    )
                elif dead_line.date() == date:
                    dead_line = get_correct_timezone_date(dead_line, TIME_ZONE)
                    duration = calc_duration(
                        midnight if dead_line.time() < schedule.start_hour
                        else schedule.start_hour,
                        dead_line.time()
                    )
                    amount = add_time(
                        amount, convert_timedelta_to_time(duration)
                    )
                else:
                    amount = add_time(amount, schedule.work_hours)
    return amount


def calc_workload_percent(schedule_hours, load_hours):
    schedule_seconds = convert_time_to_seconds(schedule_hours)
    load_seconds = convert_time_to_seconds(load_hours)
    if schedule_seconds == 0:
        raise ValueError('Сannot be zero seconds.')
    percents = (load_seconds / schedule_seconds) * 100
    return round(percents, 2)


def set_time(obj, attr, value):
    if value is not None:
        value = [int(i) for i in value.split(':')]
        setattr(obj, attr, time(*value))


def get_dates_range(min_date, max_date):
    dates_range = []
    if (min_date and max_date) is not None:
        current_date = min_date
        while current_date <= max_date:
            dates_range.append(current_date)
            current_date += timedelta(days=1)
    return dates_range


def collect_tasks(profile, date, tasks):
    date, _ = wl_models.WorkLoadModel.objects.get_or_create(
        date=date, profile=profile
    )

    for task in tasks:
        start_plan = task.date_start_plan.date()
        dead_line = task.dead_line.date()
        if dead_line > start_plan:
            date_range = get_dates_range(start_plan, dead_line)
            for d in date_range:
                wl_record, _ = wl_models.WorkLoadModel.objects.get_or_create(
                    date=d, profile=profile
                )
                wl_record.tasks.add(task)
                wl_record.save()
        elif dead_line == start_plan:
            date.tasks.add(task)
            date.save()


def signal_add_tasks(instance, date_range, profile):
    for date in date_range:
        workload, _ = wl_models.WorkLoadModel.objects.get_or_create(
            date=date, profile=profile
        )
        workload = workload
        workload.tasks.add(instance)
        workload.tasks_num = workload.tasks.count()
        workload.total_duration = get_total_duration(
            workload.tasks.all(), profile.schedule, date
        )
        workload.percents = calc_workload_percent(
            profile.schedule.work_hours, workload.total_duration
        )
        workload.save()


def signal_remove_task(workload, instance, profile):
    workload.tasks.remove(instance)
    workload.tasks_num = workload.tasks.count()
    workload.total_duration = get_total_duration(
        workload.tasks.all(), profile.schedule, workload.date
    )
    workload.percents = calc_workload_percent(
        profile.schedule.work_hours, workload.total_duration
    )
    workload.save()


def signal_exception_dates_create_and_update(instance):
    repeat_start = instance.start_date
    end_date = instance.end_date
    repeat_end = instance.repeat_end
    period = end_date - repeat_start
    repeat_frequency = instance.repeat_frequency

    if instance.is_repeatable is True:
        if repeat_end is None:
            count = 0
            while count < 100:
                wl_models.ExceptionDatesModel.objects.create(
                    exception=instance, start_date=repeat_start,
                    end_date=repeat_start + relativedelta(days=period.days)
                )
                if repeat_frequency == 'weekly':
                    repeat_start += relativedelta(weeks=1)
                elif repeat_frequency == 'monthly':
                    repeat_start += relativedelta(months=1)
                elif repeat_frequency == 'yearly':
                    repeat_start += relativedelta(years=1)
                count += 1
        else:
            while repeat_start < repeat_end:
                wl_models.ExceptionDatesModel.objects.create(
                    exception=instance, start_date=repeat_start,
                    end_date=repeat_start + relativedelta(days=period.days)
                )
                if repeat_frequency == 'weekly':
                    repeat_start += relativedelta(weeks=1)
                elif repeat_frequency == 'monthly':
                    repeat_start += relativedelta(months=1)
                elif repeat_frequency == 'yearly':
                    repeat_start += relativedelta(years=1)
    else:
        wl_models.ExceptionDatesModel.objects.create(
            exception=instance, start_date=repeat_start, end_date=end_date
        )
