import os
from sys import exit
from utils.conf import DEBUG, BASE_DIR, DUtilsKey, append_to_config, build_config, save_config

CEREMONY_PROMPT = "how do you enter the circle?"
CEREMONY_RESPONSE = "with perfect love and perfect trust"
COVEN_SENTINEL = "D-D-DEFAULT OOPS"

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

	return append_to_config({
		'PURPLE_OPTS' : {
			'connect_server' : "talk.google.com",
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

def __setup_coven(with_config):
	global COVEN_PROMPT, COVEN_SENTINEL

	conf_keys = [
		DUtilsKey("COVEN_SENTINEL", "Set your Coven's sentinel. This passphrase is used by members to request special features.",
			COVEN_SENTINEL, COVEN_PROMPT, None),
		DUtilsKey("CEREMONY_PROMPT", "Set your Ceremony's call phrase.",
			CEREMONY_PROMPT, CEREMONY_PROMPT, None),
		DUtilsKey("CEREMONY_RESPONSE", "Now, set the response to that call phrase.",
			CEREMONY_RESPONSE, CEREMONY_RESPONSE, None)
	]

	try:
		config = build_config(conf_keys, with_config)
		
		print config

		return save_config(config, with_config=with_config)

	except Exception as e:
		if DEBUG:
			print e, type(e)

	return False

if __name__ == "__main__":
	res = False

	try:
		if __setup_redis() and __setup_coven(with_config):
			res = __setup_vars(with_config)
	
	except Exception as e:
		if DEBUG:
			print e, type(e)

	exit(-1 if not res else 0)