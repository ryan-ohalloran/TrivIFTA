import paramiko
from django.conf import settings
import socks
import os
from urllib.parse import urlparse

class GeotabSFTP:
    def __init__(self, host: str = settings.SFTP_HOST, port: int = 22):
        self.host = host
        self.port = port
        self.proxy_url = os.environ.get('QUOTAGUARDSTATIC_URL')
        
        # Parse the proxy URL
        parsed_url = urlparse(self.proxy_url)
        proxy_host = parsed_url.hostname
        proxy_port = parsed_url.port
        proxy_username = parsed_url.username
        proxy_password = parsed_url.password

        # Create the proxy transport
        self.transport = paramiko.Transport((self.host, self.port))
        
        # Set up the proxy
        self.transport.connect(
            username=settings.SFTP_USERNAME,
            password=settings.SFTP_KEY,
            sock=self._get_proxy_socket(proxy_host, proxy_port, proxy_username, proxy_password)
        )
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def _get_proxy_socket(self, proxy_host, proxy_port, proxy_username, proxy_password):
        sock = socks.socksocket()
        sock.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy_host,
            port=proxy_port,
            username=proxy_username,
            password=proxy_password
        )
        sock.connect((self.host, self.port))
        return sock

    def send_to_sftp(self, csv_data: str, filename: str) -> None:
        '''
        Sends the data to the SFTP server
        '''
        try:
            with self.sftp.open(filename, 'w') as file:
                file.write(csv_data)
        except Exception as e:
            # if unsuccessful, show an error message
            raise Exception(f'Failed to send {filename} to SFTP server.\n\t{e}')
        finally:
            self.sftp.close()
            self.transport.close()