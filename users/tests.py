import json
from django.contrib.auth.models import User
from django.core import mail
from rest_framework.test import APITestCase
import urllib.parse as urlparse


class TestUsers(APITestCase):
    def __authenticate(self):
        User.objects.create_user(email='email@email.com', username='username', password='password')
        response = self.client.post('/api/v1/login/', {
            'username': 'username',
            'password': 'password'
        }, follow=True)
        tokens = response.json()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(tokens['access']))
        return tokens

    def test_protected_route(self):
        response = self.client.get('/api/v1/protected/')
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(content, {'detail': 'Authentication credentials were not provided.'})

    def test_api_login_with_wrong_password(self):
        response = self.client.post('/api/v1/login/', {
            'username': 'test',
            'password': 'test_password'
        }, HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.content), {'detail': 'No active account found with the given credentials'})

    def test_api_login_with_credentials(self):
        User.objects.create_user(username='username', password='password')
        response = self.client.post('/api/v1/login/', {
            'username': 'username',
            'password': 'password'
        }, follow=True)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access' in content and 'refresh' in content)

    def test_protected_route_with_token(self):
        self.__authenticate()
        response = self.client.get('/api/v1/protected/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'Hello, World!'})

    def test_password_reset_resets_password_success(self):
        User.objects.create_user(email='email@email.com', username='username', password='password')
        login = self.client.post('/api/v1/password-reset/', {
            'email': 'email@email.com'
        })
        self.assertEqual(login.json(), {'status': 'OK'})
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        parsed = urlparse.urlparse(message.body)
        token = urlparse.parse_qs(parsed.query)['token'][0]

        # change the password
        response = self.client.post('/api/v1/password-reset/confirm/', {
            'token': token,
            'password': 'changed_password'
        })
        self.assertEqual(response.json(), {'status': 'OK'})
        user = User.objects.get(username='username')
        self.assertTrue(user.check_password('changed_password'))

    def test_logout(self):
        token = self.__authenticate()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token['access']))
        response = self.client.post('/api/v1/logout/', {
            'refresh': token['refresh']
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'Successfully logged out'})

    def test_users_list(self):
        # create 10 users
        for i in range(1, 10):
            user = User(email='email@email{}.com'.format(i), username='username_%i' % i, password='password')
            user.save()

        self.__authenticate()
        response = self.client.get('/api/v1/users/')
        json_response = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(json_response))

    def test_create_user(self):
        self.assertEqual(User.objects.all().count(), 0)
        self.__authenticate()
        response = self.client.post('/api/v1/users/', {
            'username': 'test1',
            'email': 'email@test.com',
            'password': 'veryStrongPassword'
        })
        self.assertEqual(response.status_code, 201)
        # authentication creates a new user so it should be two users in total
        self.assertEqual(User.objects.all().count(), 2)

    def test_update_user(self):
        user = User(email='email@email.com', username='test_user', password='password')
        user.save()
        self.__authenticate()
        response = self.client.put('/api/v1/users/detail/%i/' % user.pk, {
            'username': 'test_user1',
            'email': '123@email.com'
        })
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.username, 'test_user1')
        self.assertEqual(user.email, '123@email.com')

    def test_update_password_user(self):
        # https://stackoverflow.com/questions/38845051/how-to-update-user-password-in-django-rest-framework
        user = User(email='email@email.com', username='test_user', password='password')
        user.save()
        self.__authenticate()
        response = self.client.put('/api/v1/users/update-password/%i/' % user.pk, {
            'new_password': 'strongPassword',
        })
        self.assertEqual(response.status_code, 204)
        user = User.objects.get(username='test_user')
        self.assertTrue(user.check_password('strongPassword'))

    def test_get_user(self):
        user = User(email='email@email.com', username='test_user', password='password')
        user.save()
        self.__authenticate()
        response = self.client.get('/api/v1/users/detail/%i/' % user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'pk': user.pk,
            'username': 'test_user',
            'email': 'email@email.com'
        })

    def test_delete_user(self):
        user = User(email='email@email.com', username='test_user', password='password')
        user.save()
        self.__authenticate()
        self.assertEqual(User.objects.all().count(), 2)
        response = self.client.delete('/api/v1/users/detail/%i/' % user.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(User.objects.all().count(), 1)

    def test_user_try_to_delete_yourself(self):
        self.__authenticate()
        response = self.client.delete('/api/v1/users/detail/1/')
        r_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(r_json, {
            'errors': 'You cannot delete yourself'
        })
        self.assertEqual(User.objects.all().count(), 1)