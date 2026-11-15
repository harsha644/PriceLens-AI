from django.test import TestCase
from django.contrib.auth.models import User
from django.db import connection
from rest_framework.test import APIClient
from rest_framework import status
from .models import Profile

class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.refresh_url = '/api/auth/refresh/'
        self.profile_url = '/api/auth/profile/'
        self.change_password_url = '/api/auth/change-password/'

    def test_mysql_connection(self):
        """Verify the test database runs on MySQL as strictly required."""
        self.assertEqual(connection.vendor, 'mysql')
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 + 1")
            row = cursor.fetchone()
            self.assertEqual(row[0], 2)

    def test_registration_success(self):
        data = {
            'full_name': 'Test User',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'phone': '+919876543210',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['full_name'], 'Test User')
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user__username='testuser').exists())

    def test_duplicate_username_and_email(self):
        data = {
            'full_name': 'First User',
            'username': 'uniqueuser',
            'email': 'unique@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!'
        }
        res1 = self.client.post(self.register_url, data, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Duplicate username
        dup_user_data = data.copy()
        dup_user_data['email'] = 'other@example.com'
        res2 = self.client.post(self.register_url, dup_user_data, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res2.data)

        # Duplicate email
        dup_email_data = data.copy()
        dup_email_data['username'] = 'differentuser'
        res3 = self.client.post(self.register_url, dup_email_data, format='json')
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res3.data)

    def test_login_and_wrong_password(self):
        User.objects.create_user(username='loginuser', email='login@example.com', password='GoodPassword123!')
        Profile.objects.create(user=User.objects.get(username='loginuser'), full_name='Login User')

        # Wrong password
        bad_res = self.client.post(self.login_url, {'username_or_email': 'loginuser', 'password': 'WrongPassword'}, format='json')
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Good login with username
        good_res_user = self.client.post(self.login_url, {'username_or_email': 'loginuser', 'password': 'GoodPassword123!'}, format='json')
        self.assertEqual(good_res_user.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', good_res_user.data)

        # Good login with email
        good_res_email = self.client.post(self.login_url, {'username_or_email': 'login@example.com', 'password': 'GoodPassword123!'}, format='json')
        self.assertEqual(good_res_email.status_code, status.HTTP_200_OK)

    def test_jwt_protected_access_and_refresh(self):
        user = User.objects.create_user(username='jwtuser', email='jwt@example.com', password='Password123!')
        Profile.objects.create(user=user, full_name='JWT User')

        # Unauthenticated request to profile
        unauth_res = self.client.get(self.profile_url)
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticate via login
        login_res = self.client.post(self.login_url, {'username_or_email': 'jwtuser', 'password': 'Password123!'}, format='json')
        access_token = login_res.data['tokens']['access']
        refresh_token = login_res.data['tokens']['refresh']

        # Authenticated profile request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        auth_res = self.client.get(self.profile_url)
        self.assertEqual(auth_res.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_res.data['username'], 'jwtuser')

        # Refresh token
        self.client.credentials() # clear credentials
        refresh_res = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_profile_update(self):
        user = User.objects.create_user(username='updateuser', email='update@example.com', password='Password123!')
        Profile.objects.create(user=user, full_name='Old Name', phone='+919999999999')

        self.client.force_authenticate(user=user)
        update_res = self.client.put(self.profile_url, {'full_name': 'New Full Name', 'phone': '+918888888888'}, format='json')
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_res.data['full_name'], 'New Full Name')
        self.assertEqual(update_res.data['phone'], '+918888888888')

    def test_change_password_and_logout(self):
        user = User.objects.create_user(username='pwuser', email='pw@example.com', password='OldPassword123!')
        Profile.objects.create(user=user, full_name='PW User')

        login_res = self.client.post(self.login_url, {'username_or_email': 'pwuser', 'password': 'OldPassword123!'}, format='json')
        refresh_token = login_res.data['tokens']['refresh']
        access_token = login_res.data['tokens']['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        change_res = self.client.post(self.change_password_url, {
            'old_password': 'OldPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_new_password': 'NewPassword456!'
        }, format='json')
        self.assertEqual(change_res.status_code, status.HTTP_200_OK)

        # Verify old password fails and new password works
        self.client.credentials()
        old_login = self.client.post(self.login_url, {'username_or_email': 'pwuser', 'password': 'OldPassword123!'}, format='json')
        self.assertEqual(old_login.status_code, status.HTTP_400_BAD_REQUEST)
        new_login = self.client.post(self.login_url, {'username_or_email': 'pwuser', 'password': 'NewPassword456!'}, format='json')
        self.assertEqual(new_login.status_code, status.HTTP_200_OK)

        # Test logout blacklisting
        new_refresh = new_login.data['tokens']['refresh']
        new_access = new_login.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        logout_res = self.client.post(self.logout_url, {'refresh': new_refresh}, format='json')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Attempt to use blacklisted refresh token
        bad_refresh_res = self.client.post(self.refresh_url, {'refresh': new_refresh}, format='json')
        self.assertEqual(bad_refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)
