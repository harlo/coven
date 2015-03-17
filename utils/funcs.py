import os, sys, signal, logging
from subprocess import Popen, PIPE

from utils.config import DEBUG

def get_log(log_name):
	coven_logger = logging.StreamHandler()

	mod_log = logging.getLogger(log_name)
	mod_log.addHandler(coven_logger)

def start_daemon(d_files):
	if DEBUG:
		print "starting daemon"
	
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		print e.errno
		sys.exit(1)
		
	os.chdir("/")
	os.setsid()
	os.umask(0)
	
	try:
		pid = os.fork()
		if pid > 0:
			f = open(d_files['pid'], 'w')
			f.write(str(pid))
			f.close()
			
			sys.exit(0)
	except OSError, e:
		if DEBUG:
			print e.errno
	
		sys.exit(1)
	
	si = file('/dev/null', 'r')
	so = file(d_files['log'], 'a+')
	se = file(d_files['log'], 'a+', 0)
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())

	if DEBUG:
		print ">>> PROCESS DAEMONIZED"

def stop_daemon(d_files):
	if DEBUG:
		print "stopping daemon"
		print d_files

	pid = False
	try:
		f = open(d_files['pid'], 'r')
		try:
			pid = int(f.read().strip())
		except ValueError as e:
			if DEBUG:
				print "NO PID AT %s" % d_files['pid']
	except IOError as e:
		if DEBUG:
			print "NO PID AT %s" % d_files['pid']
	
	if pid:
		if DEBUG:
			print "STOPPING DAEMON on pid %d" % pid
	
		try:
			os.kill(pid, signal.SIGTERM)
			
			if d_files['ports'] is not None:
				pids = Popen(['lsof', '-t', '-i:%d' % d_files[2]], stdout=PIPE)
				pid = pids.stdout.read().strip()
				pids.stdout.close()
				
				for p in pid.split("\n"):
					cmd = ['kill', str(p)]
					Popen(cmd)
			
			return True
		except OSError as e:
			if DEBUG:
				print "could not kill process at PID %d" % pid

	return False