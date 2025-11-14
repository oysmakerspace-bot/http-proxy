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

    @patch('requests.get')
    def test_redirect(self, mock_get):
        mock_redirect_response = MagicMock()
        mock_redirect_response.status_code = 302
        mock_redirect_response.headers = {'Location': 'http://redirected.com'}

        mock_final_response = MagicMock()
        mock_final_response.content = b'redirected content'
        mock_final_response.status_code = 200
        mock_final_response.headers = {'Content-Type': 'text/html'}

        mock_get.side_effect = [mock_redirect_response, mock_final_response]

        response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'redirected content')

    @patch('requests.get')
    def test_headers(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})

        mock_get.assert_called_once()
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['User-Agent'], 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
        self.assertEqual(headers['Host'], 'example.com')

    @patch('requests.get')
    def test_redirect_chain(self, mock_get):
        mock_redirect1 = MagicMock()
        mock_redirect1.status_code = 301
        mock_redirect1.headers = {'Location': 'http://redirected1.com'}

        mock_redirect2 = MagicMock()
        mock_redirect2.status_code = 302
        mock_redirect2.headers = {'Location': 'http://redirected2.com'}

        mock_final_response = MagicMock()
        mock_final_response.content = b'final content'
        mock_final_response.status_code = 200
        mock_final_response.headers = {'Content-Type': 'text/html'}

        mock_get.side_effect = [mock_redirect1, mock_redirect2, mock_final_response]

        response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'final content')

    @patch('requests.get')
    def test_relative_redirect(self, mock_get):
        mock_redirect = MagicMock()
        mock_redirect.status_code = 302
        mock_redirect.headers = {'Location': '/redirected'}

        mock_final_response = MagicMock()
        mock_final_response.content = b'relative redirect content'
        mock_final_response.status_code = 200
        mock_final_response.headers = {'Content-Type': 'text/html'}

        mock_get.side_effect = [mock_redirect, mock_final_response]

        response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'relative redirect content')

        # Check that the redirect URL was called with the correct headers
        redirect_call = mock_get.call_args_list[1]
        self.assertEqual(redirect_call[0][0], 'http://example.com/redirected')
        self.assertEqual(redirect_call[1]['headers']['User-Agent'], 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
        self.assertEqual(redirect_call[1]['headers']['Host'], 'example.com')

    @patch('requests.get')
    def test_too_many_redirects(self, mock_get):
        mock_redirect = MagicMock()
        mock_redirect.status_code = 302
        mock_redirect.headers = {'Location': 'http://redirected.com'}

        mock_get.side_effect = [mock_redirect] * 6

        response = self.app.post('/', json={'method': 'GET', 'destination': 'http://example.com'})
        self.assertEqual(response.status_code, 508)
        self.assertIn(b'Too many redirects', response.data)

if __name__ == '__main__':
    unittest.main()
