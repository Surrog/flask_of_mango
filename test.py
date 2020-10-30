import unittest
import requests as req


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
            r = req.get('http://localhost:5000/status/' + str(request_id))
            self.assertNotEqual(r, "id not found")
            print(r.content)
            return
        self.assertTrue(False, "failed to load file")


if __name__ == '__main__':
    unittest.main()
