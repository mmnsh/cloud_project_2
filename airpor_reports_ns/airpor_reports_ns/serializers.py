from rest_framework import serializers


class RequestLoggerSerializer(serializers.Serializer):
    headers = serializers.CharField(required=False, allow_null=True)
    resolver_match = serializers.CharField(required=False, allow_null=True)
    user = serializers.CharField(required=False, allow_null=True)
    method = serializers.CharField(required=False, allow_null=True)
    content_type = serializers.CharField(required=False, allow_null=True)
    content_params = serializers.CharField(required=False, allow_null=True)
    body = serializers.CharField(required=False, allow_null=True)


class ResponseLoggerSerializer(serializers.Serializer):
    headers = serializers.CharField(required=False, allow_null=True)
    request = serializers.CharField(required=False, allow_null=True)
    data = serializers.CharField(required=False, allow_null=True)
    status_code = serializers.CharField(required=False, allow_null=True)
    exception = serializers.CharField(required=False, allow_null=True)
    renderer_context = serializers.CharField(required=False, allow_null=True)
