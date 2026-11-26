"""Exercise the actual local HTTP adapter with a tiny dataset."""
import http.client
import json
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path

from src.backend import Backend
from src.server import make_handler
from tests.testhamza import write_fixture, calendar


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        write_fixture(Path(cls.temp.name))
        handler = make_handler(Backend(cls.temp.name))
        handler.log_message = lambda *args: None
        cls.server = HTTPServer(('127.0.0.1', 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def request(self, method, path, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            conn.request(method, path, json.dumps(body) if body is not None else None,
                         {'Content-Type': 'application/json'})
            reply = conn.getresponse()
            return reply.status, json.loads(reply.read())
        finally:
            conn.close()

    def test_health_and_cases(self):
        self.assertEqual(self.request('GET', '/health'), (200, {'status': 'OK'}))
        status, rows = self.request('GET', '/cases')
        self.assertEqual((status, rows[0]['case_id']), (200, 'demo'))

    def test_route_and_network(self):
        status, data = self.request('POST', '/route', {'case_id': 'demo', 'target': 2})
        self.assertEqual((status, data['cost']), (200, 7))
        status, data = self.request('POST', '/network', {'case_id': 'demo'})
        self.assertEqual((status, data['cost']), (200, 5))

    def test_campaign(self):
        status, data = self.request('POST', '/campaign', {'case_id': 'demo', 'calendar': calendar()})
        self.assertEqual((status, len(data['days'])), (200, 7))

    def test_official_calendar_is_api_default(self):
        status, data = self.request('POST', '/campaign', {'case_id': 'demo'})
        self.assertEqual(status, 200)
        self.assertEqual(data['days'][1]['closed_roads'], [2])
        self.assertEqual(data['days'][1]['input']['changed_minutes'], {'0': 2, '1': 2, '2': 11})
        self.assertIsNone(data['days'][6]['load'])

    def test_g_endpoints(self):
        self.assertEqual(self.request('POST', '/chain', {'case_id': 'demo'})[1]['cost'], 1000)
        self.assertEqual(self.request('POST', '/drum', {'case_id': 'demo', 'length': 4})[1]['price'], 10)

    def test_missing_and_invalid(self):
        self.assertEqual(self.request('GET', '/missing')[0], 404)
        self.assertEqual(self.request('POST', '/route', {'case_id': 'demo', 'target': 99})[0], 422)
        self.assertEqual(self.request('POST', '/route', [1])[0], 422)
        self.assertEqual(self.request('POST', '/campaign', {'case_id': 'demo', 'calendar': {}})[0], 422)


if __name__ == '__main__':
    unittest.main()
