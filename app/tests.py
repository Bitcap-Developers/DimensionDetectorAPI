from django.test import TestCase,Client
import json

# Create your tests here.


class TestDimensionDetector(TestCase):

## testing the about endpoint for dimensiod detection	
	def test_aboutEndpoint(self):
		client=Client()
		payload = {'url1':'https://scontent.fdel7-1.fna.fbcdn.net/v/t34.0-0/s261x260/20289803_1573727455990823_868522136_n.jpg?oh=b80a983392887776a1d3fa67979ca982&oe=5975BFFF' , 'url2':'https://scontent.fdel7-1.fna.fbcdn.net/v/t34.0-0/s261x260/20206272_1573727562657479_2084465416_n.jpg?oh=9a6ee62317cfec2f5fde95d7ae18dda8&oe=59759294'}
		payload = json.dumps(payload)
		response = client.post('/about', payload)
		print response.content
		self.assertEqual(response.status_code,200)




