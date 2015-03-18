import re, os, redis
import tornado.ioloop, tornado.httpserver, tornado.web
from multiprocessing import Process

from models.coven_purple_client import CovenPurpleClient
from utils.config import get_config, DEBUG
from utils.funcs import start_daemon, stop_daemon

class CovenAPIApplication(tornado.web.Application, CovenPurpleClient):
	def __init__(self):
		if DEBUG:
			print "init API application"

		self.lookup = redis.StrictRedis(host='localhost', port=os.environ['REDIS_PORT'], db=0)
		self.api_routes = {			
			'twilio' : {
				'endpoints' : ["chal_response"],
				'handler' : self.TwilioRouter
			}
		}

	class TwilioRouter(tornado.web.RequestHandler):
		def post(self, route):
			if DEBUG:
				print "twilio routed!"
				print route
				print self.reqest

			if route == "chal_response":
				# XXX: extract chal response from SMS
				chal_response = "dummy chal response"
				self.application.lookup.publish('CHAL_RESPONSE_QUEUE', chal_response)

	def start_API_client(self):
		if DEBUG:
			print "start API client"

		CovenPurpleClient.__init__(self)

		p = Process(target=self.start_purple_client)
		p.start()

		tornado.web.Application.__init__(self, 
			[(re.compile('/%s/(%s)' % (e, "|".join(self.api_routes[e]['endpoints']))), self.api_routes[e]['handler']) for e in self.api_routes.keys()])
		
		API_PORT = os.environ['API_PORT']
		API_DAEMON, API_OPTS = get_config(['API_DAEMON', 'API_OPTS'])
		server = tornado.httpserver.HTTPServer(self)

		try:
			server.bind(API_PORT)
		except Exception as e:
			from fabric.api import settings, local
			from fabric.context_managers import hide

			with settings(warn_only=True):
				local("kill $(lsof -t -i:%d)" % API_PORT)

			server.bind(API_PORT)

		start_daemon(API_DAEMON)
		server.start(API_OPTS['num_processes'])
		tornado.ioloop.IOLoop.instance().start()

	def stop_API_client(self):
		self.stop_purple_client()
		stop_daemon(get_config('API_DAEMON'))