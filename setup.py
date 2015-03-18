import os
from sys import exit, argv
from utils.conf import DEBUG, BASE_DIR, DUtilsKey, append_to_config, build_config, save_config

CEREMONY_PROMPT = "how do you enter the circle?"
CEREMONY_RESPONSE = "with perfect love and perfect trust"
COVEN_SENTINEL = "D-D-DEFAULT OOPS"
JABBER_SERVER = "talk.google.com"

def __setup_redis():
	import re

	redis_port = int(os.environ['REDIS_PORT'])
	redis_conf = []
	redis_replace = [
		("daemonize no", "no", "yes"),
		("pidfile /var/run/redis.pid", "redis", "redis_%d" % redis_port),
		("port 6379", "6379", str(redis_port)),
		("logfile \"\"", "\"\"", "/var/log/redis_%d.log" % redis_port),
		("dir ./", "./", "/var/redis/%d" % redis_port)
	]

	try:
		with open(os.path.join(BASE_DIR, "lib", "redis-stable", "redis.conf"), 'rb') as r:
			for line in r.read().splitlines():
				for rr in redis_replace:
					if line == rr[0]:
						line = line.replace(rr[1], rr[2])
						
						if DEBUG:
							print "replaced: %s" % line
						break

				redis_conf.append(line)
	except Exception as e:
		if DEBUG:
			print "could not build redis config from template"
			print e, type(e)

		return False

	try:
		with open(os.path.join(BASE_DIR, "lib", "redis-stable", "%d.conf" % redis_port), 'wb+') as r:
			r.write("\n".join(redis_conf))

		return True
	except Exception as e:
		if DEBUG:
			print "could not save %d.conf" % redis_port
			print e, type(e)

	return False

def __setup_vars(with_config):
	MONITOR_ROOT = os.path.join(BASE_DIR, ".monitor")

	res, config = append_to_config({
		'PURPLE_OPTS' : {
			'port' : '443',
			'old_ssl' : True
		},
		'PURPLE_DAEMON' : {
			'log' : os.path.join(MONITOR_ROOT, "purple.log.txt"),
			'pid' : os.path.join(MONITOR_ROOT, "purple.pid.txt")
		},
		'API_OPTS' : {
			'num_processes' : 10
		},
		'API_DAEMON' : {
			'log' : os.path.join(MONITOR_ROOT, "api.log.txt"),
			'pid' : os.path.join(MONITOR_ROOT, "api.pid.txt")
		}
	}, with_config=with_config)

	if res:
		config['PURPLE_OPTS']['connect_server'] = config['JABBER_SERVER']
		del config['JABBER_SERVER']

		config['PURPLE_OPTS']['jabber_id'] = config['JABBER_ID']
		del config['JABBER_ID']

		return save_config(config, with_config=with_config)

	return False

def __setup_twitter(consumer_key, consumer_secret):
	authorization_url = "http://api.twitter.com/oauth/authorize"
	request_token_url = "http://api.twitter.com/oauth/request_token"
	access_token_url = "http://api.twitter.com/oauth/access_token"

	import oauth2

	try:
		consumer = oauth2.Consumer(consumer_key, consumer_secret)
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
		return dict(urlparse.parse_qsl(content))

	except Exception as e:
		if DEBUG:
			print e, type(e)

	return None

def __setup_coven(with_config):
	conf_keys = [
		DUtilsKey("COVEN_SENTINEL", "Set your Coven's sentinel. This passphrase is used by members to request special features.",
			COVEN_SENTINEL, COVEN_PROMPT, None),
		DUtilsKey("CEREMONY_PROMPT", "Set your Ceremony's call phrase.",
			CEREMONY_PROMPT, CEREMONY_PROMPT, None),
		DUtilsKey("CEREMONY_RESPONSE", "Now, set the response to that call phrase.",
			CEREMONY_RESPONSE, CEREMONY_RESPONSE, None),
		DUtilsKey("JABBER_SERVER", "What is the hostname of your Jabber server?",
			JABBER_SERVER, JABBER_SERVER, None),
		DUtilsKey("JABBER_ID", "What is your jabber ID?",
			"none", "none", None)
	]

	for t in ["ACCESS_TOKEN_KEY", "ACCESS_TOKEN_SECRET", "CONSUMER_KEY", "CONSUMER_SECRET"]:
		conf_keys.append(DUtilsKey("TWITTER_%s" % t, "Twitter %s" % t.lower().replace("_", ""),
			"none", "none", None))

	try:
		config = build_config(conf_keys, with_config)
		if not save_config(config, with_config=with_config):
			return False

		twitter_credentials = __setup_twitter(config['TWITTER_CONSUMER_KEY'], config['TWITTER_CONSUMER_SECRET'])

		if twitter_credentials is not None:
			return append_to_config({'TWITTER_OAUTH_CREDENTIALS' : twitter_credentials }, with_config=with_config)

	except Exception as e:
		if DEBUG:
			print e, type(e)

	return False

if __name__ == "__main__":
	res = False
	with_config = os.path.join(BASE_DIR, ".config.json")

	if len(argv) == 2 and os.path.exists(argv[1]):
		with_config = argv[1]

	try:
		if __setup_redis() and __setup_coven(with_config):
			if __setup_vars(with_config):
				from fabric.api import settings, local

				with settings(warn_only=True):
					local("chmod 0400 %s" % with_config)

				res = True
	
	except Exception as e:
		if DEBUG:
			print e, type(e)

	exit(-1 if not res else 0)