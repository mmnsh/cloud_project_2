from django.shortcuts import render

# Create your views here.

from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']


class UserInfoView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        uus = UserUpdateSerializer(data=request.data, partial=True, instance=request.user)
        uus.is_valid(raise_exception=True)
        uus.save()
        return Response(UserSerializer(request.user).data)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        urs = UserRegisterSerializer(data=request.data)
        urs.is_valid(raise_exception=True)
        user = urs.save()
        user.set_password(urs['password'].value)
        user.save()
        return Response(UserSerializer(user).data)
