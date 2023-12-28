from django.db import models
from .utils import encrypt_data, decrypt_data
from django.core.exceptions import ValidationError
from pandas import DataFrame

MAX_EMAIL_SENDERS = 1

class EmailRecipient(models.Model):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=255, default="IFTA Compliance Team")

    def __str__(self):
        return self.email

class EmailSender(models.Model):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=255, default="IFTA Compliance Service")
    smtp_server = models.CharField(max_length=255)
    smtp_port = models.IntegerField()
    smtp_user = models.CharField(max_length=255)
    smtp_password = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.pk and EmailSender.objects.count() >= MAX_EMAIL_SENDERS:
            raise ValidationError(f"Cannot create more than {MAX_EMAIL_SENDERS} email senders.")
        
        self.smtp_password = encrypt_data(self.smtp_password)
        super().save(*args, **kwargs)

    def get_smtp_password(self):
        return decrypt_data(self.smtp_password)

    def __str__(self) -> str:
        return self.email

class IftaEntry(models.Model):
    vin = models.CharField(max_length=17)
    reading_date = models.DateField()
    reading_time = models.TimeField()
    odometer = models.IntegerField()
    jurisdiction = models.CharField(max_length=2)

    class Meta:
        unique_together = (('vin', 'reading_date', 'reading_time'),)

    @staticmethod
    def save_all_entries(self, entries: DataFrame) -> None:
        """
        Save all entries in the dataframe to the database
        """
        for _, row in entries.iterrows():
            try:
                # Create or update an IftaEntry object from the row
                IftaEntry.objects.update_or_create(
                    vin=row['VIN'],
                    reading_date=row['ReadingDate'],
                    reading_time=row['ReadingTime'],
                    defaults={
                        'odometer': row['Odometer'],
                        'jurisdiction': row['Jurisdiction']
                    }
                )
            except Exception as e:
                # Log the error and continue with the next row
                print(f"Error creating or updating entry from row {row}: {e}")
    
    def __str__(self) -> str:
        return f"{self.vin} {self.reading_date} {self.reading_time} {self.odometer} {self.jurisdiction}"
