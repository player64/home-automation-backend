from django.contrib.auth.models import User


class EmailAuth:

    """Authenticate a user by an exact match on the email and password"""

    @staticmethod
    def authenticate(email=None, password=None):
        """
        Get an instance of `User` based off the email and verify the
        password
        """
        try:
            user = User.objects.get(email=email)

            if user.check_password(password):
                return user

            return None
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user(user_id):
        """
        Used by the Django authentication system to retrieve a user instance
        """
        try:
            user = User.objects.get(pk=user_id)

            if user.is_active:
                return user

            return None
        except User.DoesNotExist:
            return None
