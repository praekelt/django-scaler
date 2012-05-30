import time

from django.test import TestCase
from django.test.client import Client
from django.core.files import File as DjangoFile
from django.core.urlresolvers import reverse
from django.conf import settings


class ScalerTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_auto_scaler(self):
        """Middleware redirects requests by itself"""
        # Use delay to smooth out anomalies. A page may render in 5ms and the
        # next time in 20ms because of many reasons. A large enough delay
        # flattens the discrepancy ratio.
        for i in range(0, 20):
            response = self.client.get('/?delay=0.1')
            self.assertEqual(response.status_code, 200)        

        # Start making slow requests. We expect a redirection after X requests.
        # We don't care exactly when since many things may influence response
        # time. The math does indicate that redirection is expected sometime.
        for i in range(0, 10):
            response = self.client.get('/?delay=1.0')
            if response.status_code == 302:
                stamp = time.time()
        self.assertEqual(response.status_code, 302)

        # Make requests every 2 seconds. Redirects are expected for 
        # 10 seconds.
        now = time.time()
        while now - settings.DJANGO_SCALER['redirect_for'] < stamp:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 302)
            time.sleep(2)
            now = time.time()

        # Time has elapsed. Redirection is disabled for the next request.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # And the next request will pass as well since the trend cache is 
        # clean. 
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_excplicit_scaler(self):
        """Middleware is instructed to redirect X slowest URLs"""
        # Do calls so we can decide which URLs are slowest.
        for i in range(0, 20):
            response = self.client.get('/?delay=0.1')
            self.assertEqual(response.status_code, 200)        
            response = self.client.get('/scaler-test-one/?delay=0.3')
            self.assertEqual(response.status_code, 200)        
            response = self.client.get('/scaler-test-two/?delay=0.5')
            self.assertEqual(response.status_code, 200)        

        # Set the redirect_n_slowest_function
        settings.DJANGO_SCALER['redirect_n_slowest_function'] = lambda: 2

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)        
        response = self.client.get('/scaler-test-one/')
        self.assertEqual(response.status_code, 302)        
        response = self.client.get('/scaler-test-two/')
        self.assertEqual(response.status_code, 302)
