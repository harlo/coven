import twitter, oauth2
from utils.config import get_config, DEBUG

class CovenTwitterClient(twitter.Api):
	def __init__(self, lookup=None):
		if DEBUG:
			print "twitter client..."

		c_keys = ["ACCESS_TOKEN_KEY", "ACCESS_TOKEN_SECRET", "CONSUMER_SECRET", "CONSUMER_KEY"]
		ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET, CONSUMER_SECRET, CONSUMER_KEY = get_config(["TWITTER_%s" % k for k in c_keys])

		credentials = {}
		missing_credentials = []

		try:
			for c in c_keys:
				if locals(c) is None:
					missing_credentials.append(c)

				credentials[c.lower()] = locals[c]

			if len(missing_credentials) > 0:
				if not __init_twitter_account():
					if DEBUG:
						print "could not make twiiter happen."

					return

				for c in missing_credentials:
					locals[c] = get_config("TWITTER_%s" % c)
					credentials[c.lower()] = locals[c]

			twitter.Api.__init(self, **credentials)
		except Exception as e:
			if DEBUG:
				print e, type(e)

			return

		if lookup is not None:
			self.lookup = lookup

	def __init_twitter_account():
		if DEBUG:
			print "init twitter account"

		authorization_url = "http://api.twitter.com/oauth/authorize"
		request_token_url = "http://api.twitter.com/oauth/request_token"
		access_token_url = "http://api.twitter.com/oauth/access_token"

		try:
			consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
			client = oauth2.Client(consumer)
		except Exception as e:
			if DEBUG:
				print e, type(e)

			return False

		res, content = client.request(request_token_url, "POST", body="oauth_callback=oob")
		if int(res['status']) != 200:
			if DEBUG:
				print "no, invalid response from twtter: %s" % res['status']

			return False

		import urlparse
		from fabric.operations import prompt

		token_request = dict(urlparse.parse_qsl(content))

		if DEBUG:
			print "TOKEN REQUEST:"
			print token_request

		print "Visit the following URL in a browser.  Come back and paste in the PIN here."
		print "*****"
		print "%s?oauth_token=%s" % (authorization_url, token_request['oauth_token'])
		print "*****"
		oauth_pin = prompt("PIN: ")

		try:
			token = oauth2.Token(token_request['oauth_token'], token_request['oauth_token_secret'])
			token.set_verifier(oauth_pin)
			client = oauth2.Client(consumer, token)

			res, content = client.request(access_token_url, "POST")
			access_token = dict(urlparse.parse_qsl(content))

			if DEBUG:
				print "TOKEN CREATED:"
				print access_token

			return __append_to_config({
				'TWITTER_CONSUMER_SECRET' : access_token['oauth_token_secret'],
				'TWITTER_CONSUMER_KEY' : access_token['oauth_token']
			})

		except Exception as e:
			if DEBUG:
				print e, type(e)

		return False

	def get_chal_response(self):
		if DEBUG:
			print "get chal response"

		# do whatever to trigger a chal-response and then
		# self.lookup.publish('CHAL_RESPONSE_QUEUE', chal_response)

	def send_tweet(self, message):
		if DEBUG:
			print "send tweet"
			print message

		res = self.PostUpdate(message)
		
		if DEBUG:
			print res

	def follow_user(self, twitter_id):
		if DEBUG:
			print "follow user %s" % twitter_id