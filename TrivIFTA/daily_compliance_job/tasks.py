# daily_compliance_job/tasks.py

from celery import shared_task
from django.core.management import call_command
import datetime

@shared_task
def run_daily_job_task(date: datetime.date, remove_unchanged:bool = False, send_email:bool = False, save_to_db:bool = False, send_to_ftp:bool = False) -> str:
    command_options = [date]
    if remove_unchanged:
        command_options.append('--remove-unchanged')
    if send_email:
        command_options.append('--send-email')
    if save_to_db:
        command_options.append('--save-to-db')
    if send_to_ftp:
        command_options.append('--send-to-ftp')

    # Run the command with the date argument and the specified options
    return call_command('run_daily_job', *command_options)