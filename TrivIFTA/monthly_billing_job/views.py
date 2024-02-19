from django.shortcuts import render
from rest_framework.decorators import api_view
from django.http import JsonResponse, HttpResponseServerError
from rest_framework.response import Response
from .tasks import run_monthly_billing_job_task
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def get_company_bills(request) -> JsonResponse | HttpResponseServerError:
    try:
        month = request.data.get('month', None)
        year = request.data.get('year', None)

        # run the job and get the JSON data
        json_data = run_monthly_billing_job_task(month, year)

        return Response(json_data, content_type='application/json')
    
    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError(e)