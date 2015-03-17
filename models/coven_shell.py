import cmd, os, json, re
from sys import argv

from utils.conf import DEBUG
from utils.vars import CEREMONY_STATUS as status

class CovenShell(cmd.Cmd):
	def __init__(self, lookup):
		self.lookup = lookup

		try:
			self.introduction_request_queue = self.lookup.pubsub()
			self.introduction_request_queue.subscribe(**{'INTRODUCTION_REQUEST_QUEUE' : self.__on_introduction_requested})
		except Exception as e:
			if DEBUG:
				print e, type(e)

		cmd.Cmd.__init__(self)

	def do_ceremony(self, line):
		if DEBUG:
			print "Ceremony"
			print line

		if line == "start":
			self.__set_status(CEREMONY_STATUS.started)
			print "Your Ceremony has begun.  You know what to do."
		elif line == "stop":
			self.__set_status(CEREMONY_STATUS.stopped)
			print "Your Ceremony ended."

	def do_info(self, line):
		if DEBUG:
			print "info!"

		show_all = False

		if line.strip() == "":
			show_all = True

		# is API up?
		if show_all or line == "api":
			print "API Status:"

		# is Purple up?
		if show_all or line == "jabber":
			print "Jabber Client Status:"

		# show client OTR fingerprint
		if show_all or line == "fingerprint":
			print "OTR Fingerprint:"

		# how many members in coven?
		if show_all or line == "members":
			print "Coven Members:"
			self.do_whois("")

		# how many tweets?
		if show_all or line == "tweets":
			print "Tweets Tweeted:"

		# how many 2fa tokens issued?  (and to whom?)
		if show_all or line == "2fa":
			print "2FA Tokens Issued:"

	def do_whois(self, line):
		if DEBUG:
			print "whois"
			print line

		show_all = False
		if line.strip() == "":
			show_all = True

		# print member username, twitter handle, fingerprint

	def __set_status(self, status):
		self.lookup.set('CEREMONY_STATUS', status)

	def __get_status(self):
		return self.lookup.get('CEREMONY_STATUS')

	def __on_introduction_requested(self, introduction):
		try:
			username, fingerprint, twitter_id = json.loads(introduction['data'])
		except Exception as e:
			if DEBUG:
				print "An error occurred :("
			return

		print "%s (@%s on twitter) wants to join the Coven." % (username, twitter_id)
		print "presenting fingerprint:"
		print "\n%s\n" % fingerprint.upper()
		
		accept_fingerprint = raw_input("accept %s and follow @%s on twitter? (y/N) " % (username, twitter_id))
		if accept_fingerprint != "y":
			print "Member rejected.\n\n"
			return
	
		try:
			self.lookup.publish('MEMBERSHIP_QUEUE', introduction['data'])
		except Exception as e:
			if DEBUG:
				print e, type(e)

		print "\n"
		grant_2fa = "Grant 2FA Token Privileges to @%s? (y/N) " % twitter_id
		if grant_2fa == "y":
			try:
				self.lookup.publish('2FA_PRIVILEGES_QUEUE', fingerprint)
			except Exception as e:
				if DEBUG:
					print e, type(e)

		print "\n\n"

	def preloop(self):
		if DEBUG:
			print "preloop"

		cmd.Cmd.preloop(self)

	def postloop(self):
		if DEBUG:
			print "postloop"

		cmd.Cmd.postloop(self)