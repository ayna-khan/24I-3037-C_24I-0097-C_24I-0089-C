"""The interface server: same data as Hamza's loader, pages and API on one origin."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from frontend.server import PAGES, STATIC, make_server
from src.backend import Backend
from src.models import InvalidInputError
from tests.testhamza import write_fixture


class FrontendServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        write_fixture(cls.temp.name)
        cls.server = make_server(cls.temp.name, 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def request(self, method, path, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        try:
            conn.request(method, path, body=None if body is None else json.dumps(body))
            response = conn.getresponse()
            return response.status, response.getheader('Content-Type'), response.read()
        finally:
            conn.close()

    def test_every_page_is_served(self):
        for path, (name, kind) in PAGES.items():
            status, content_type, body = self.request('GET', path)
            self.assertEqual(status, 200, path)
            self.assertTrue(content_type.startswith(kind))
            self.assertEqual(body, (Path(STATIC) / name).read_bytes())

    def test_other_files_are_not_served(self):
        for path in ('/../server.py', '/server.py', '/static/app.js'):
            self.assertEqual(self.request('GET', path)[0], 404, path)

    def test_indexed_loader_matches_the_original(self):
        status, _, body = self.request('POST', '/case', {'case_id': 'demo'})
        self.assertEqual(status, 200)
        expected = json.loads(json.dumps(Backend(self.temp.name).case('demo')))
        self.assertEqual(json.loads(body), expected)

    def test_campaign_route_through_the_site(self):
        status, _, body = self.request('POST', '/campaign', {'case_id': 'demo'})
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)['days']), 7)

    def test_unknown_case_is_reported(self):
        status, _, body = self.request('POST', '/case', {'case_id': 'nope'})
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(body)['status'], 'INVALID')
        with self.assertRaises(InvalidInputError):
            Backend(self.temp.name).case('nope')

    def test_missing_dataset_stops_with_a_message(self):
        with tempfile.TemporaryDirectory() as empty, self.assertRaises(SystemExit):
            make_server(empty, 0)


if __name__ == '__main__':
    unittest.main()
