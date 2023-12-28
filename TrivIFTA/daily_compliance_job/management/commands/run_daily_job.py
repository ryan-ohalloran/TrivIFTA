from django.core.management.base import BaseCommand
from daily_compliance_job.models import IftaEntry
from daily_compliance_job.services.geotab import MyGeotabAPI
from daily_compliance_job.services.ftp import GeotabFTP
from daily_compliance_job.services.email import EmailService
from daily_compliance_job.services.ifta import IftaDataCollection
import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the daily compliance job to generate IFTA reports'

    def add_arguments(self, parser):
        # arugments for the date, test mode, and removing unchanged entries
        parser.add_argument('from_date', 
            type=str, 
            help='Date for which the report should be run (format YYYY-MM-DD)',)
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run the command in test mode without sending to FTP',)
        parser.add_argument(
            '--remove-unchanged',
            action='store_true',
            help='Remove entries whose odometer readings do not change',)

    def handle(self, *args, **options):
        # Parsing the date arguments
        from_date_str = options['from_date']

        # Default to yesterday's date if no date was provided
        if from_date_str is None:
            logger.info("No date provided. Defaulting to yesterday's date.")
            from_date = datetime.datetime.now() - datetime.timedelta(days=1)
            to_date = datetime.datetime.now()
        else:
            try:
                from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d')
                to_date = from_date + datetime.timedelta(days=1)
            except ValueError as e:
                logger.error(f'Invalid date format in command: {e}')
                return

        # Set the time to 0:00:00
        from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = to_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Instantiate MyGeotabAPI
        my_geotab_api = MyGeotabAPI()

        # Logic to generate CSV
        geotab_ifta_data_collection = my_geotab_api.to_ifta_data_collection(from_date, to_date)
        full_df = geotab_ifta_data_collection.to_dataframe()

        full_csv_data = full_df.to_csv(index=False)
        file_name = f'Ohalloran_{from_date.year}_{from_date.month:02d}_{from_date.day:02d}.csv'

        # If the test argument was provided, print the dataframe and return
        if options['test']:
            test_mode(full_csv_data, file_name, options, geotab_ifta_data_collection, from_date)
            return

        # Send the CSV to the FTP server
        # send_to_ftp(full_csv_data, file_name, from_date)

        # send email to recipients
        subject = f'IFTA Report Success {file_name} --- {from_date.month}/{from_date.day}/{from_date.year}'
        body = f'''IFTA report for {from_date.month}/{from_date.day}/{from_date.year} sent successfully to FTP.
        \n\nPlease see the attached file for the report.
        \n\nThank you,
        \nTrivista IFTA Compliance Team
        '''

        email_service = EmailService(subject, body, attachment=full_csv_data, attachment_name=file_name)
        # send the email, and if it is successful, save the entries to the database
        if email_service.send():
            IftaEntry.save_all_entries(full_df)
            logger.info('Successfully saved entries to database.')

def test_mode(full_csv_data: str, file_name: str, options: dict, geotab_ifta_data_collection: IftaDataCollection, date: datetime.date) -> None:
    '''
    Run the command in test mode
    '''
    logger.info('Test mode. Not sending to FTP server.')
    logger.info(f'Generating CSV for {file_name}...')

    subject = "IFTA Report Test"
    body = f"This is a test email. Please ignore. Attached is the IFTA report for date: {date.month}/{date.day}/{date.year}"

    # create reduced df if the remove_unchanged argument was provided
    if options['remove_unchanged']:
        reduced_df = geotab_ifta_data_collection.to_dataframe(remove_nonmoving_vehicles=True)
        reduced_csv_data = reduced_df.to_csv(index=False)
        logger.info(reduced_df)
        email_service = EmailService(subject, body, attachment=reduced_csv_data, attachment_name=file_name)
        email_service.send()
        return

    email_service = EmailService(subject, body, attachment=full_csv_data, attachment_name=file_name)
    email_service.send()
    return

def send_to_ftp(full_csv_data: str, file_name: str, date: datetime.date) -> None:
    ftp = GeotabFTP()
    try:
        ftp.send_to_ftp(full_csv_data, file_name)
    except Exception as e:
        # If FTP job fails, send an email to the recipients and return
        logger.error(f'Failed to send {file_name} to FTP server.\n\t{e}')
        subject = f"IFTA Report Failure {file_name} --- {date.month}/{date.day}/{date.year}"
        body = f'''Failed to send IFTA report for {date.month}/{date.day}/{date.year} to FTP.
                \n\nPlease check the logs for more details.
                \nThank you,
                \nTrivista IFTA Compliance Team
                '''

        email_service = EmailService(subject, body)
        email_service.send()
        return

    logger.info(f'Successfully sent {file_name} to FTP server🔥')