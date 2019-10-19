#from app.py import *
#from bs4 import BeautifulSoup
import requests, unittest
from bs4 import BeautifulSoup

#pip3 install requests
#pip3 install BeautifulSoup4
#pip3 install bs4

# UNITTEST all tests must start with test**
# LEVERAGE assert -> self.assertTrue()

# python3 test_web.py

WORDLIST = "wordlist.txt"
SITE = "http://localhost:5000/"


class TestWebFunctions(unittest.TestCase):

	def testRootPage(self):
		# This test validates that the Root Directory Page Response to a HTTP 200 Response Code
		loginPage = requests.get(SITE)
		assert(loginPage.status_code == 200)

	def test_validateLoginPage(self):
		# This test validates that the Login Page Response to a HTTP 200 Response Code
		loginPage = requests.get(SITE+"login")
		assert(loginPage.status_code == 200)

	def test_validateSpellCheckPage(self):
		# This test validates that the Spell Check Page Response to a HTTP 200 Response Code
		spellCheckPage = requests.get(SITE+"spell_check")
		assert(spellCheckPage.status_code == 200)

	def test_validateRegisterPage(self):
		# This test validates that the Register Page Response to a HTTP 200 Response Code
		registerPage = requests.get(SITE+"register")
		assert(registerPage.status_code == 200)
	
	def test_registerUser(self):
		# Tests and validates that a user can properly register a unique username
		username = 'username1'
		password= 'password'
		mfa='11111111111'
		client = requests.session()
		#client.get(SITE+"register")
		response = client.get(SITE+"register").text
		responseText = BeautifulSoup(response,'html.parser')
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		payload=('uname=%s&pword=%s&mfa=%s&csrf_token=%s' % (username, password, mfa, csrf_token))
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		postResponse =  client.post(url=SITE+"register",headers=headers,data=payload).text 
		soupResult = BeautifulSoup(postResponse,'html.parser')
		soupAnswer = soupResult.find(id='result').text.strip()
		self.assertEqual(soupAnswer,'success')

	def test_registerUserTwice(self):
		# Tests and validates that a User should NOT be able to register the same user name more than once.
		username = 'username1'
		password= 'password'
		mfa='11111111111'
		client = requests.session()
		#client.get(SITE+"register")
		response = client.get(SITE+"register").text
		responseText = BeautifulSoup(response,'html.parser')
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		payload=('uname=%s&pword=%s&mfa=%s&csrf_token=%s' % (username, password, mfa, csrf_token))
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		postResponse =  client.post(url=SITE+"register",headers=headers,data=payload).text 

		# RePOSTing the request to ensure failure occurs is same user is registered again
		postResponse =  client.post(url=SITE+"register",headers=headers,data=payload).text 
		soupResult = BeautifulSoup(postResponse,'html.parser')
		soupAnswer = soupResult.find(id='result').text.strip()
		self.assertEqual(soupAnswer,'failure')		

	def test_loginUser(self):
		# Tests and validates whether a User can login properly
		username = 'username2'
		password= 'password'
		mfa='11111111111'
		client = requests.session()
		#client.get(SITE+"register")
		response = client.get(SITE+"register").text
		responseText = BeautifulSoup(response,'html.parser')
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		payload=('uname=%s&pword=%s&mfa=%s&csrf_token=%s' % (username, password, mfa, csrf_token))
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		postResponse =  client.post(url=SITE+"register",headers=headers,data=payload).text 
		soupResult = BeautifulSoup(postResponse,'html.parser')
		soupAnswer = soupResult.find(id='result').text.strip()
		self.assertEqual(soupAnswer,'success')
		loginResponse = client.get(SITE+"login").text
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		payload=('uname=%s&pword=%s&mfa=%s&csrf_token=%s' % (username, password, mfa, csrf_token))
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		loginResponse =  client.post(url=SITE+"login",headers=headers,data=payload).text 
		loginResult = BeautifulSoup(loginResponse,'html.parser')
		loginAnswer = loginResult.find(id='result').text.strip()
		self.assertEqual(loginAnswer,'Successful Authentication')

	def test_spellCheck(self):
		# Tests and validates that a user can properly use the spellchecker in the application
		username = 'username3'
		password= 'password'
		mfa='11111111111'
		client = requests.session()
		#client.get(SITE+"register")
		response = client.get(SITE+"register").text
		responseText = BeautifulSoup(response,'html.parser')
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		payload=('uname=%s&pword=%s&mfa=%s&csrf_token=%s' % (username, password, mfa, csrf_token))
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		postResponse =  client.post(url=SITE+"register",headers=headers,data=payload).text 
		soupResult = BeautifulSoup(postResponse,'html.parser')
		soupAnswer = soupResult.find(id='result').text.strip()
		self.assertEqual(soupAnswer,'success')
		loginResponse = client.get(SITE+"login").text
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		payload=('uname=%s&pword=%s&mfa=%s&csrf_token=%s' % (username, password, mfa, csrf_token))
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		loginResponse =  client.post(url=SITE+"login",headers=headers,data=payload).text 
		loginResult = BeautifulSoup(loginResponse,'html.parser')
		loginAnswer = loginResult.find(id='result').text.strip()
		self.assertEqual(loginAnswer,'Successful Authentication')
		response = client.get(SITE+"spell_check").text
		responseText = BeautifulSoup(response,'html.parser')
		csrf_token= responseText.find('input', {'name':'csrf_token'})['value']
		spellCheckWords='tacos%0D%0Anonsensewords'
		spellCheckValidate = "['nonsensewords']"
		spellButton='Check+Spelling'
		spellCheckPayload = ('textbox=%s&csrf_token=%s&submit_button=%s') %(spellCheckWords,csrf_token,spellButton)
		spellCheckResponse = client.post(SITE+'spell_check',headers=headers,data=spellCheckPayload).text
		spellCheckResult = BeautifulSoup(spellCheckResponse,'html.parser')
		spellCheckResults = spellCheckResult.find("p").findNext("p").get_text().strip()
		self.assertEqual(spellCheckResults,spellCheckValidate)	

if __name__=='__main__':
	unittest.main()
	



