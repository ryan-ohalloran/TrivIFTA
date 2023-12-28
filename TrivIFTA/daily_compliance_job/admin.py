from django import forms
from django.contrib import admin
from django.contrib import messages
from .models import EmailRecipient, EmailSender
from django.core.exceptions import ValidationError

@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'name')
    search_fields = ('email', 'name')

@admin.register(EmailSender)
class EmailSenderAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'smtp_server', 'smtp_port', 'smtp_user')
    search_fields = ('name', 'email')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'smtp_password':
            kwargs['widget'] = forms.PasswordInput
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            messages.error(request, e.message)