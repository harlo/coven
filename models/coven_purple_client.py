import potr, re, os, json

from models.coven_twitter_client import CovenTwitterClient
from utils.conf import get_config, DEBUG, BASE_DIR
from utils.funcs import get_log

DEFAULT_POLICY_FLAGS = {
	'ALLOW_V1' : False,
	'ALLOW_V2' : True,
	'REQUIRE_ENCRYPTION' : True
}

PROTOCOL = "xmpp"
MMS=1024

# OR WHATEVER... I JUST NEED SOME VARS
TRUST_LEVELS = {
	'IN_COVEN' : 2,
	'UNKNOWN' : 0
}

COVEN_NAME = get_config('COVEN_NAME')

class CovenPurpleClient(object):
	def __init__(self):
		self.logger = get_log('purple')

	class CovenOTRContext(potr.context.Context):
		def __init__(self, account, peer):
			print account
			print peer

			potr.context.Context.__init(self, account, peer)

		def getPolicy(self, key):
			if key in DEFAULT_POLICY_FLAGS:
				return DEFAULT_POLICY_FLAGS[key]

			return False

		def inject(self, message, appdata=None):
			if DEBUG:
				print "INJECT!"
				print message
				print appdata

		def setState(self, new_state):
			potr.context.Context.setState(self, new_state)

	class CovenOTRAccount(potr.context.Account):
		def __init__(self, jid):
			global PROTOCOL, MMS
			
			potr.context.Account.__init__(self, jid, PROTOCOL, MMS)
			self.keyFilePath = os.path.join(BASE_DIR, ".otr", "%s.%s" % (jid.getNode(), jid.getDomain()))

			try:
				with open(self.keyFilePath, 'rb') as t:
					self.trusts = json.loads(t.read())
			except Exception as e:
				if DEBUG:
					print e, type(e)

				self.trusts = {}

		def loadPrivateKey(self):
			if DEBUG:
				print "load private key"

			try:
				with open("%s.key3" % self.keyFilePath, 'rb') as k:
					return potr.crypt.PK.parsePrivateKey(k.read())[0]
			except IOError as e:
				if DEBUG:
					print e

			return None

		def savePrivateKey(self):
			if DEBUG:
				print "save private key"

			try:
				with open("%s.key3" % self.keyFilePath, 'wb+') as k:
					k.write(self.getPrivkey().serializePrivateKey())
			except IOError as e:
				if DEBUG:
					print e

		def saveTrusts(self):
			if DEBUG:
				print "save trust"

			try:
				with open("%s.trusts.json" % self.keyFilePath, 'wb+') as t:
					t.write(json.dumps(self.trusts))
			except Exception as e:
				if DEBUG:
					print e, type(e)

	def tweet_message(self, username, message):
		if DEBUG:
			print "tweet message"
			print message

		otr_ctx = self.__get_context_for_user(username)
		if otr_ctx[1] != TRUST_LEVELS['IN_COVEN']:
			return

		self.twitter_client.send_tweet(message)

	def request_introduction(self, username, twitter_id):
		if DEBUG:
			print "request_introduction"

		try:
			otr_ctx = self.__get_context_for_user(username)

			# XXX: how to extract fingerprint from otr_ctx?
			self.lookup.publish('INTRODUCTION_REQUEST_QUEUE', json.dumps([username, fingerprint, twitter_id]))

		except Exception as e:
			if DEBUG:
				print e, type(e)

	def request_chal_response(self, username):
		if DEBUG:
			print "request chal response"
			print username

		otr_ctx = self.__get_context_for_user(username)
		if otr_ctx[1] != TRUST_LEVELS['IN_INNER_SANCTUM']:
			return

		CHAL_RESPONSE_QUEUE = self.__get_chal_response_queue()
		CHAL_RESPONSE_QUEUE.append(username)

		self.lookup.set('CHAL_RESPONSE_QUEUE', json.dumps(list(set(CHAL_RESPONSE_QUEUE))))
		self.twitter_client.get_chal_response()

	def __get_chal_response_queue(self):
		try:
			return json.loads(self.lookup.get('CHAL_RESPONSE_QUEUE'))
		except Exception as e:
			if DEBUG:
				# WARN.
				print "Something is wonky with the chal-response queue?"
				print e, type(e)
		
		return []

	def __get_context_for_user(self, username):
		if not username in self.purple_contexts:
			self.purple_contexts[username] = self.CovenOTRContext(self.purple_account, username)

		otr_ctx = self.purple_contexts[username]

		# XXX: how to extract key, fingerprint from otr_ctx?
		return otr_ctx, self.purple_account.getTrust(key, fingerprint)

	def __send_message(self, message, recipient):
		if DEBUG:
			print "send message"
			print recipient, message

		# XXX: not 100% how to get jid from purple_account
		otr_ctx = self.__get_context_for_user(self.purple_account.jid)
		if otr_ctx.state == potr.context.STATE_ENCRYPTED:
			if DEBUG:
				print "encrypting a message"

			otr_ctx.sendMessage(0, message)
		else:
			if DEBUG:
				print "chat status is not encrypted."

			# IF THIS IS THE TYPE OF MESSAGE WE CAN SEND OUT, GO AHEAD.
			# IF NOT, DO NOTHING.

	def __broadcast_message(self, message, recipients=None):
		if DEBUG:
			print "broadcast message"
			print message

		if recipients is None:
			recipients = self.purple_contexts.keys()

		for recipient in recipients:
			self.__send_message(message, recipient)		

	def __on_chal_response_received(self, chal_response):
		if DEBUG:
			print "on chal response received"

		try:
			self.__broadcast_message(chal_response['data'], json.loads(self.lookup.get('CHAL_RESPONSE_QUEUE')))
			self.lookup.delete('CHAL_RESPONSE_QUEUE')
		except Exception as e:
			if DEBUG:
				print e, type(e)

	def __on_member_accepted(self, member):
		if DEBUG:
			print "on member accepted"

		try:
			username, fingerprint, twitter_id = json.loads(member['data'])
			otr_ctx = self.__get_context_for_user(username)

			# XXX: how to extract key, fingerprint from otr_ctx?
			self.purple_account.setTrust(key, fingerprint, TRUST_LEVELS['IN_COVEN'])
			self.twitter_client.follow_user(twitter_id)

		except Exception as e:
			if DEBUG:
				print e, type(e)

	def __on_2fa_priviledge_granted(self, username, fingerprint):
		if DEBUG:
			print "on 2FA priviledge granted"

		otr_ctx = self.__get_context_for_user(username)

		# XXX: how to extract key, fingerprint from otr_ctx?
		# lookup user by username
		# if found, and fingerprint matches fingerprint from otr_ctx
		# and trust level == in_coven:
		# add to existing trust level

		current_trust = self.purple_account.getTrust(key, fingerprint)
		if current_trust >= TRUST_LEVELS['IN_COVEN']:
			self.purple_account.setTrust(key, fingerprint, TRUST_LEVELS['IN_INNER_SANCTUM'])

	def __on_connected(self, purple_con, con_type):
		if DEBUG:
			print "on connected"
			print dir(purple_con)
			print con_type
		
		self.core.auth = self.core.auth(self.jid.getNode(), get_config('PURPLE_JABBER_PWD'), 
			resource=self.jid.getResource(), sasl=1, on_auth=self.__on_authenticated)
		self.core.RegisterHandler('message', self.__on_message)

	def __on_authenticated(self, purple_con, auth):
		if DEBUG:
			print "on authenticated"

	def __on_connection_failed(self):
		if DEBUG:
			print "on connection failed"

	def __on_connect_progress(self, text, step, step_count):
		if DEBUG:
			print "on connect progress"
			print text, step, step_count

	def __on_disconnected(self):
		if DEBUG:
			print "on disconnected"

	def __on_message(self, purple_con, message):
		if DEBUG:
			print "on message"
			print dir(message)

		otr_ctx = self.__get_context_for_user(message.getFrom())
		msg_encrypted = False

		try:
			otr_message = otr_ctx[0].receiveMessage(message.getBody())
			msg_encrypted = True
		except potr.context.UnencryptedMessage as e:
			if DEBUG:
				print e

		if not msg_encrypted:
			if DEBUG:
				print "MESSAGE WAS NOT ENCRYPTED, THOUGH."

			return
		
		if otr_message[0] is None:
			return

		if DEBUG:
			print "WE CAN USE THIS MESSAGE."
			print otr_message

		has_ceremony_sentinel = re.match(re.compile("%s\s@(\w+)" % CEREMONY_SENTINEL), otr_message[0])
		if has_ceremony_sentinel:
			self.request_introduction(message.getFrom(), has_ceremony_sentinel.group())
			return

		if 'COVEN_NAME' not in locals.keys():
			locals['COVEN_NAME'] = get_config('COVEN_NAME')

		if otr_message[0] == "~*%s*~" % COVEN_NAME:
			self.request_chal_response(message.getFrom())
			return
		
		self.tweet_message(message.getFrom(), otr_message[0])

	def __on_buddy_list_updated(self, update_type, name=None, alias=None):
		if DEBUG:
			print "on buddy list updated"
			print update_type, name, alias

	def start_purple_client(self):
		import nbxmpp

		try:
			self.twitter_client = CovenTwitterClient(lookup=self.lookup)
		except Exception as e:
			if DEBUG:
				print e, type(e)
				print "Failure initing twitter client"

			#return
		
		PURPLE_JABBER_ID, PURPLE_OPTS, PURPLE_DAEMON = get_config(['PURPLE_JABBER_ID', 'PURPLE_OPTS', 'PURPLE_DAEMON'])

		try:
			idle_queue = nbxmpp.idlequeue.get_idlequeue()

			self.callbacks = nbxmpp.Smacks(self)
			self.jid = nbxmpp.protocol.JID(PURPLE_JABBER_ID)
			self.purple_account = self.CovenOTRAccount(self.jid)
		
			self.client = nbxmpp.NonBlockingClient(self.jid.getDomain(), idle_queue, caller=self)
			self.con = self.client.connect(self.__on_connected, self.__on_connection_failed, secure_tuple=('tls', '', '', 2, None))
	
		except Exception as e:
			if DEBUG:
				print e, type(e)
				print "Failure executing nbxmpp."

			return
		
		self.purple_contexts = {}

		'''
			Subscribe to all the info channels we need for message-routing
		'''
		try:
			self.chal_response_queue = self.lookup.pubsub()
			self.chal_response_queue.subscribe(**{'CHAL_RESPONSE_QUEUE' : self.__on_chal_response_received})

			self.membership_queue = self.lookup.pubsub()
			self.membership_queue.subscribe(**{'MEMBERSHIP_QUEUE' : self.__on_member_accepted})

			self._2fa_priviledge_queue = self.lookup.pubsub()
			self._2fa_priviledge_queue.subscribe(**{'2FA_PRIVILEGES_QUEUE' : self.__on_2fa_priviledge_granted})

		except Exception as e:
			if DEBUG:
				print e, type(e)
				print "Failure initing redis channel"

			return

	def stop_purple_client(self):
		if DEBUG:
			print "stop purple client"

		if hasattr(self, "client"):
			try:
				self.client.start_disconnect()
			except Exception as e:
				if DEBUG:
					print e, type(e)

				return False

		return True