from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'email']


class UserPasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128, write_only=True, required=True)

    def save(self, pk, **kwargs):
        password = self.validated_data['new_password']
        # user = self.context['request'].user
        user = User.objects.get(pk=pk)
        user.set_password(password)
        user.save()
