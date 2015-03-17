from sys import argv, exit
from multiprocessing import Process

from models.coven_api_application import CovenAPIApplication
from utils.config import DEBUG

class Coven(CovenAPIApplication):
	def __init__(self):
		CovenAPIApplication.__init__(self)
	
	def connect(self):
		from models.coven_shell import CovenShell

		if DEBUG:
			print "connecting to coven..."

		try:
			coven_shell = CovenShell(self.lookup)
			coven_shell.cmdloop()
			
			return True
		except Exception as e:
			if DEBUG:
				print e, type(e)

		return False

	def start(self):
		if DEBUG:
			print "starting coven..."

		try:
			p = Process(target=self.start_API_client)
			p.start()

			return True
		except Exception as e:
			if DEBUG:
				print e, type(e)

			print "Could not start coven.  Exiting."

		return False

	def stop(self):
		if DEBUG:
			print "stopping coven"

		self.stop_API_client()
		return True

if __name__ == "__main__":
	res = False
	coven = Coven()

	if len(argv) == 2:		
		if argv[1] in ["stop", "restart"]:
			res = coven.stop()

		if argv[1] in ["start", "restart"]:
			res = coven.start()
	else:
		res = coven.connect()

	exit(0 if res else -1)