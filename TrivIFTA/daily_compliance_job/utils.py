from cryptography.fernet import Fernet
from django.conf import settings
import csv
import json

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

def convert_csv_to_json(csv_data: str) -> str:
    # return the csv data as a json object of the form: {"text": csv_data}
    return json.dumps({"text": csv_data})