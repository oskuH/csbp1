import logging
import json
from django.contrib.auth import get_user_model

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        # https://stackoverflow.com/questions/59462109/django-custom-logging-handler-class-cant-be-picked-up
        from .models import Log
        json_formatted_log = self.format(record)
        log_data = json.loads(json_formatted_log)
        
        User = get_user_model()
        user_instance = None
        try:
            user_instance = User.objects.get(username=log_data.get('user'))
        except User.DoesNotExist:
            user_instance = None

        log_entry = {
            'timestamp': log_data.get('asctime'),
            'interaction_id': log_data.get('interaction_id'),
            'application': log_data.get('application'),
            'code_location': log_data.get('code_location'),
            'user': user_instance,
            'event_type': log_data.get('event_type'),
            'event_code': log_data.get('event_code'),
            'levelname': log_data.get('levelname'),
            'description': log_data.get('description'),
            'json_log': json_formatted_log
        }

        Log.objects.create(**log_entry)