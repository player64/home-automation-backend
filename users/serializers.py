from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.generics import get_object_or_404


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'email']


class NewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class UserPasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128, write_only=True, required=True)

    def save(self, pk, **kwargs):
        password = self.validated_data['new_password']
        user = get_object_or_404(User, pk=pk)
        user.set_password(password)
        user.save()
