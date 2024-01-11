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
            nargs='?',
            default=None,
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
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send the report via email',)
        parser.add_argument(
            '--save-to-db',
            action='store_true',
            help='Save the report to the database',)
        parser.add_argument(
            '--send-to-ftp',
            action='store_true',
            help='Send the report to the FTP server',)

    def handle(self, *args, **options) -> str:
        # Parsing the date arguments
        from_date_str = options['from_date']

        # Default to yesterday's date if no date was provided
        if from_date_str is None:
            DAYS_BACK = 4
            from_date = datetime.datetime.now() - datetime.timedelta(days=DAYS_BACK)
            to_date = datetime.datetime.now() - datetime.timedelta(days=DAYS_BACK - 1)
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

        csv_data = full_csv_data
        # if the remove_unchanged argument was provided, create a reduced dataframe
        if options['remove_unchanged']:
            reduced_df = geotab_ifta_data_collection.to_dataframe(remove_nonmoving_vehicles=True)
            reduced_csv_data = reduced_df.to_csv(index=False)
            csv_data = reduced_csv_data
        
        # if the test argument was provided, print the dataframe and return (and email if the email argument was provided)
        if options['test']:
            send_email = bool(options['send_email'])
            test_mode(full_csv_data, file_name, from_date, send_email=send_email)
            return

        # send the CSV to the FTP server
        if options['send_to_ftp']:
            if not send_to_ftp(csv_data, file_name, from_date):
                raise Exception('Failed to send data to FTP server')

        # send email to recipients
        if options['send_email']:
            if not send_success_email(csv_data, file_name, bool(options['send_to_ftp']), from_date, geotab_ifta_data_collection.total_vehicles, geotab_ifta_data_collection.num_nonmoving_vehicles):
                raise Exception('Failed to send success email')
            
        # save entries to database if save_to_db argument was provided
        #   Note: the full dataframe is always saved to the database
        if options['save_to_db']:
            IftaEntry.save_all_entries(entries=full_df)
            logger.info('Successfully saved entries to database.')
        
        return csv_data

def test_mode(csv_data: str, file_name: str, date: datetime.date, send_email: bool = False) -> None:
    '''
    Run the command in test mode
    '''
    logger.info('Test mode. Not sending to FTP server.')
    logger.info(f'Generating CSV for {file_name}...')
    print(csv_data)
    # send the email if the email argument was provided
    if send_email:
        subject = "IFTA Report Test"
        body = f"This is a test email. Please ignore. Attached is the IFTA report for date: {date.month}/{date.day}/{date.year}"
        email_service = EmailService(subject, body, date=date, attachment=csv_data, attachment_name=file_name)
        email_service.send()

    return

def send_to_ftp(full_csv_data: str, file_name: str, date: datetime.date) -> bool:
    '''
    Send the CSV to the FTP server

    Returns True if the CSV was sent successfully, False otherwise
    '''
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
        return False

    logger.info(f'Successfully sent {file_name} to FTP server🔥')
    return True

def send_success_email(full_csv_data: str, file_name: str, sent_to_ftp: bool, date: datetime.date, total_vehhicles: int, num_nonmoving_vehicles: int) -> bool:
    '''
    Send an email to the recipients to notify them of a successful CSV generation
    
    Returns True if the email was sent successfully, False otherwise
    '''
    subject = f"IFTA Report Success {file_name} --- {date.month}/{date.day}/{date.year}"
    if not sent_to_ftp:
        body = f'''IFTA report for {date.month}/{date.day}/{date.year} sucessfully generated.
                \n\nPlease see the attached file for the report.
                \n\nReport statistics:
                \n\tTotal vehicles: {total_vehhicles}
                \n\tNumber of non-moving vehicles: {num_nonmoving_vehicles}
                \n\nThank you,
                \nTrivista IFTA Compliance Team
                '''
    elif sent_to_ftp:
        body = f'''IFTA report for {date.month}/{date.day}/{date.year} sucessfully generated and sent to FTP.
                \n\nPlease see the attached file for the report sent to the Idealease FTP server.
                \n\nReport statistics:
                \n\tTotal vehicles: {total_vehhicles}
                \n\tNumber of non-moving vehicles: {num_nonmoving_vehicles}
                \n\nThank you,
                \nTrivista IFTA Compliance Team
                '''

    email_service = EmailService(subject, body, date=date, attachment=full_csv_data, attachment_name=file_name)
    if email_service.send():
        return True
    return False