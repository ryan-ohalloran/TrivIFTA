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

        print(f"Parsed QuotaGuard URL: host={proxy_host}, port={proxy_port}, username={proxy_username}")

        # Set up the SOCKS5 proxy
        self.sock = socks.socksocket()
        self.sock.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy_host,
            port=proxy_port,
            username=proxy_username,
            password=proxy_password
        )

        # Connect to the proxy server
        print(f"Connecting to proxy server {proxy_host}:{proxy_port}")
        self.sock.connect((self.host, self.port))
        print(f"Connected to proxy server {proxy_host}:{proxy_port}")

        # Create a paramiko transport object using the proxy-connected socket
        self.transport = paramiko.Transport(self.sock)

        # Connect to the SFTP server
        print(f"Connecting to SFTP server {self.host}:{self.port}")
        self.transport.connect(username=settings.SFTP_USERNAME, password=settings.SFTP_KEY)
        print(f"Connected to SFTP server {self.host}:{self.port}")

        # Open an SFTP session
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        print("Opened SFTP session")

    def send_to_sftp(self, csv_data: str, filename: str) -> None:
        '''
        Sends the data to the SFTP server
        '''
        try:
            with self.sftp.open(filename, 'w') as file:
                file.write(csv_data)
        except Exception as e:
            # if unsuccessful, show an error message
            print(f'Failed to send {filename} to SFTP server.\n\t{e}')
            raise
        finally:
            self.sftp.close()
            self.transport.close()