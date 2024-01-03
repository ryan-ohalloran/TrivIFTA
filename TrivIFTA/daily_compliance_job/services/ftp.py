from ftplib import FTP
import pandas as pd
from django.conf import settings
import io

class GeotabFTP(FTP):
    def __init__(self, host: str = settings.FTP_HOST):
        super().__init__(host)
        self.login(user=settings.FTP_USERNAME, passwd=settings.FTP_KEY)

    def send_to_ftp(self, data: pd.DataFrame, filename: str) -> None:
        '''
        Sends the data to the FTP server
        '''
        # convert the data to a csv string
        data_csv = data.to_csv(index=False).encode('utf-8')

        try:
            # send the data to the FTP server
            self.storbinary(f'STOR {filename}', io.BytesIO(data_csv))
        except Exception as e:
            # if unsuccessful, show an error message
            raise Exception(f'Failed to send {filename} to FTP server.\n\t{e}')