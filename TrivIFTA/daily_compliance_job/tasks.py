# daily_compliance_job/tasks.py

from celery import shared_task
from django.core.management import call_command
import datetime

@shared_task
def run_daily_job_task():
    # Logic for running the daily job
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    # Run the command with the date argument and the remove-unchanged flag
    call_command('run_daily_job', yesterday_str, '--remove-unchanged', '--send-email', '--save-to-db', '--send-to-ftp')