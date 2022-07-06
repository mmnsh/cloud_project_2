import json

from django.conf import settings
from fluent import event, sender

from .serializers import RequestLoggerSerializer, ResponseLoggerSerializer


class LoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def emit_event(self, data, model_name, event_name, *args, **kwargs):
        for key, value in kwargs.items():
            data.update({key: value})
        fluent_sender = sender.FluentSender(
            "mongo.{}".format(model_name), host=settings.FLUENTD_HOST
        )
        event.Event(event_name, data, sender=fluent_sender)

    def __call__(self, request):
        response = self.get_response(request)
        try:
            request_data = RequestLoggerSerializer(request).data
        except Exception as e:
            return response
        try:
            response_data = ResponseLoggerSerializer(response).data
            response_data.update({"request": json.dumps(request_data)})
            self.emit_event(response_data, "request", "logger")
        except Exception as e:
            pass
        return response
