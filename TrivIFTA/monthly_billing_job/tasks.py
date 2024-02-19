from django.core.management import call_command

def run_monthly_billing_job_task(month: int, year: int) -> str:
    command_options = [month, year]
    return call_command('run_monthly_billing_job', *command_options)