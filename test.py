import unittest
import requests as req
import time
import json


class TestService(unittest.TestCase):
    def test_invalid_id(self):
        r = req.get('http://localhost:5000/status/0')
        print(r)
        self.assertFalse(r.ok)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.content, b'{"error": "Id not found"}')

    def test_send_request(self):
        with open("test.csv", 'rb') as f:
            request_id = req.post('http://localhost:5000/process_values', files={"input": f})
            self.assertTrue(request_id.ok)
            print("received id: " + str(request_id.content))
            time.sleep(2)
            r = req.get(b'http://localhost:5000/status/' + request_id.content)
            self.assertNotEqual(r.content, b'{"error": "Id not found"}')
            value = json.loads(r.content)
            print(value)
            self.assertNotEqual(value["input"], None)
            self.assertNotEqual(value["id"], None)
            self.assertNotEqual(value["do_work1"], None)
            self.assertNotEqual(value["do_work2"], None)
            self.assertNotEqual(value["do_work3"], None)
            self.assertNotEqual(value["finished"], None)
            return

if __name__ == '__main__':
    unittest.main()
