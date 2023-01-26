from django.test import TestCase
from django.urls import reverse

from accounts.models import Shopper
from store.models import Product


class StoreTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Sneakers de Erevan',
            price=10,
            stock=10,
            description='De superbes Chaussures',
        )

    def test_products_are_shown_on_index_page(self):
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.product.name, str(resp.content))
        self.assertIn(self.product.thumbnail_url(), str(resp.content))

    def test_connexion_link_shown_user_not_connected(self):
        resp = self.client.get(reverse('index'))
        self.assertIn('Connexion', str(resp.content))

    def test_redirect_when_anonymous_access_cart_view(self):
        resp = self.client.get(reverse('store:cart'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, f'{reverse("accounts:login")}?next={reverse("store:cart")}', status_code=302)


class StoreLoggedInTest(TestCase):
    def setUp(self):
        self.user = Shopper.objects.create_user(
            email='patrick@gmail.com',
            first_name='Patrick',
            last_name='Smith',
            password='123456',
        )

    def test_valid_login(self):
        data = {'email': 'patrick@gmail.com', 'password': '123456'}
        resp = self.client.post(reverse('accounts:login'), data=data)
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get(reverse('index'))
        self.assertIn('Mon profil', str(resp.content))

    def test_invalid_login(self):
        data = {'email': 'patrick@gmail.com', 'password': '123456'}
        resp = self.client.post(reverse('accounts:login'), data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/login.html')

    def test_profile_change(self):
        self.client.login(email='patrick@gmail.com',
                          password='123456')
        data = {
            'email': 'patrick@gmail.com',
            'password': '123456',
            'first_name': 'Patrick',
            'last_name': 'Martin'
        }

        resp = self.client.post(reverse('accounts:profile'), data=data)
        self.assertEqual(resp.status_code, 302)
        patrick = Shopper.objects.get(email='patrick@gmail.com')
        self.assertEqual(patrick.last_name, 'Martin')






