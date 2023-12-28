from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet():
    # Generate a key if it doesn't exist
    if not settings.FERNET_KEY:
        settings.FERNET_KEY = Fernet.generate_key()
    return Fernet(settings.FERNET_KEY)

def encrypt_data(data):
    f = get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt_data(data):
    f = get_fernet()
    return f.decrypt(data.encode()).decode()