import unittest
import os
from unittest.mock import patch, MagicMock
from app.proxy import app

class ProxyTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        os.environ.pop('ALLOWED_IPS', None)

    def tearDown(self):
        os.environ.pop('ALLOWED_IPS', None)

    @patch('requests.get')
    def test_get_request(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = b'example content'
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'example content')

    @patch('requests.post')
    def test_post_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.content = b'{"status": "success"}'
        mock_response.status_code = 201
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        response = self.app.post('/', json={'method': 'POST', 'destination': 'http://example.com', 'key': 'value'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, b'{"status": "success"}')

    def test_missing_method(self):
        response = self.app.post('/', json={'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'method and destination are required', response.data)

    def test_missing_destination(self):
        response = self.app.post('/', json={'method': 'GET'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'method and destination are required', response.data)

    def test_invalid_method(self):
        response = self.app.post('/', json={'method': 'PUT', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid method specified', response.data)

    def test_allowed_ip(self):
        os.environ['ALLOWED_IPS'] = '127.0.0.1'
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
            self.assertEqual(response.status_code, 200)

    def test_disallowed_ip(self):
        os.environ['ALLOWED_IPS'] = '192.168.1.1'
        response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Source IP not allowed', response.data)

if __name__ == '__main__':
    unittest.main()
