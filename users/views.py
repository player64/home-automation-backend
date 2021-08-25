import os

import requests
from django.contrib.auth.models import User
from django_rest_passwordreset.views import ResetPasswordRequestToken, ResetPasswordConfirm
from rest_framework import status, mixins, generics
from rest_framework.exceptions import ValidationError
from rest_framework.generics import UpdateAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers import UserSerializer, UserPasswordChangeSerializer


class HelloView(APIView):
    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)


class ApiLogout(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({
            'status': 'Successfully logged out'
        })


class UserList(APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        # prevent self deletion
        if request.user.pk == self.kwargs.get('pk'):
            raise ValidationError({'errors': 'You cannot delete yourself'})
        return self.destroy(request, *args, **kwargs)


class ChangePasswordView(UpdateAPIView):
    serializer_class = UserPasswordChangeSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(pk=self.kwargs.get('pk'))

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(GenericAPIView):
    """
    This class is replacing ResetPasswordRequestToken behaviour to add captcha validation.
    This might cause exceptions if happened uncomment original URL in users/urls pass
    """
    # disable authentication request
    permission_classes = ()

    @staticmethod
    def _validate_captcha(recaptcha_response) -> bool:
        captcha_secret = os.environ.get('CAPTCHA_SECRET')
        if not captcha_secret:
            return False
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': captcha_secret,
                'response': recaptcha_response
            })
        if not response.headers['Content-Type'].startswith('application/json'):
            return False
        json_response = response.json()
        if 'success' in json_response:
            return True
        return False

    @staticmethod
    def _raise_exception(error):
        return Response('It\'s a problem with library resetting the password., %s' % str(error),
                        status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        recaptcha_response = request.data.get('recaptcha_response')
        if not recaptcha_response or not self._validate_captcha(recaptcha_response):
            raise ValidationError('This request cannot be handled, there is not valid captcha response')
        try:
            reset_password = ResetPasswordRequestToken()
            return reset_password.post(request=request)
        except Exception as e:
            return self._raise_exception(e)

    def put(self, request, *args, **kwargs):
        try:
            confirm_reset_password = ResetPasswordConfirm()
            return confirm_reset_password.post(request=request)
        except Exception as e:
            return self._raise_exception(e)
