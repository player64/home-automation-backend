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
        return response.json()

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
        token = self.__authenticate()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token['access']))
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

        # login with the new password
        response = self.client.post('/api/v1/login/', {
            'username': 'username',
            'password': 'changed_password'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access' in response.json() and 'refresh' in response.json())

    def test_logout(self):
        token = self.__authenticate()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token['access']))
        response = self.client.post('/api/v1/logout/', {
            'refresh': token['refresh']
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'Successfully logged out'})
