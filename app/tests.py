from django.test import TestCase,Client
import json

# Create your tests here.


class TestDimensionDetector(TestCase):

## testing the about endpoint for dimensiod detection	
	def test_aboutEndpoint(self):
		payload = {'url1':'https://scontent-lhr3-1.xx.fbcdn.net/v/t35.0-12/21640562_10203865554036793_129594673_o.jpg?oh=8ed44762a98254d86c7f9fb06c64ca82&oe=59BE33B0' , 'url2':'https://scontent-lhr3-1.xx.fbcdn.net/v/t35.0-12/21640416_10203865554676809_840353446_o.jpg?oh=0d21d305a85bdba615c00763c5649389&oe=59BE3C88'}
		payload = json.dumps(payload)
		response = self.client.post('/about',data=payload,content_type='application/json')
		print response.content
		self.assertEqual(response.status_code,200)




