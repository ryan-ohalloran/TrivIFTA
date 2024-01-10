from rest_framework.decorators import api_view
from rest_framework.response import Response
from .tasks import run_daily_job_task
from .utils import convert_csv_to_json
from django.http import JsonResponse, HttpResponseServerError
from .models import IftaEntry
import logging
import os
from .serializers import IftaEntrySerializer

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_config(request) -> JsonResponse:
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    return Response({'API_BASE_URL': API_BASE_URL}, content_type='application/json')

@api_view(['POST'])
def run_job(request) -> JsonResponse | HttpResponseServerError:
    try:
        # Extract the options from the request data
        date = request.data.get('date', None)
        remove_unchanged = request.data.get('remove_unchanged', False)
        send_email = request.data.get('send_email', False)
        save_to_db = request.data.get('save_to_db', False)
        send_to_ftp = request.data.get('send_to_ftp', False)

        # Run the job and get the CSV data
        csv_data = run_daily_job_task(date, remove_unchanged, send_email, save_to_db, send_to_ftp)

        # Convert the CSV data to JSON
        json_data = convert_csv_to_json(csv_data)

        # Return the data in the response
        return Response(json_data, content_type='application/json')
    
    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError(e)
    
@api_view(['GET'])
def get_entries_by_date(request, date):
    entries = IftaEntry.objects.filter(reading_date=date)
    serializer = IftaEntrySerializer(entries, many=True)
    return Response(serializer.data)