import twitter, oauth2
from utils.config import get_config, DEBUG

class CovenTwitterClient(twitter.Api):
	def __init__(self, lookup=None):
		if DEBUG:
			print "twitter client..."

		credentials = {}
		for t in ["ACCESS_TOKEN_KEY", "ACCESS_TOKEN_SECRET", "CONSUMER_SECRET", "CONSUMER_KEY"]:
			credentials[t.lower()] = get_config("TWITTER_%s" % t)

		try:
			twitter.Api.__init__(self, **credentials)
		except Exception as e:
			if DEBUG:
				print e, type(e)

			return

		if lookup is not None:
			self.lookup = lookup

	def get_chal_response(self):
		if DEBUG:
			print "get chal response"

		# XXX: do whatever to trigger a chal-response and then
		# self.lookup.publish('CHAL_RESPONSE_QUEUE', chal_response)

	def send_tweet(self, tweet):
		if DEBUG:
			print "send tweet"
			print tweet

		res = self.PostUpdate(tweet)
		
		if DEBUG:
			print res

	def follow_user(self, twitter_id):
		if DEBUG:
			print "follow user %s" % twitter_id

	def get_followers(self):
		if DEBUG:
			print "get followers"