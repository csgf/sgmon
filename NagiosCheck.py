#!/usr/bin/python
import abc,logging
import sys,signal
# aggiungere rotazione dei LOG ?
# DONE 29-10-13
#from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler

"Exit statuses" 
#OK=0
#WARNING=1
#CRITICAL=2
#UNKNOWN=3

class NagiosCheck(object):
    "base class for my nagios plugins"
    __metaclass__ = abc.ABCMeta

    OK=0
    WARNING=1
    CRITICAL=2
    UNKNOWN=3

    def __init__(self,wT,cT,oF,lL=logging.DEBUG):
        "get thresholds, initialize working variables"

        self.warningThreshold=wT
        self.criticalThreshold=cT

        self.outMsg="Check not started"
        # setup logger
        # basic logger, doesn't perform rotation 
        # can't keep both - would be double logging
        #logging.basicConfig(level=lL,
        #            format='%(asctime)-4s %(levelname)-4s %(message)s',
        #            datefmt='%Y-%m-%d %H:%M:%S',
        #            filename=oF,
        #            filemode='a')
        self.logger=logging.getLogger('NagiosCheck')
        
        #ch = logging.StreamHandler()
        #ch.setLevel(lL)
	# timed rotating seems not to work as it apparently requires continous running
        #logHandler = TimedRotatingFileHandler(oF,when="D",interval=1,backupCount=7)
        logHandler = RotatingFileHandler(oF,mode='a',maxBytes=19999,backupCount=7)
        
	#formatter=        
	#ch.setFormatter(formatter)
	logHandler.setFormatter(logging.Formatter('%(asctime)-4s %(levelname)-4s %(message)s'))
        self.logger.addHandler(logHandler)
        #logger.addHandler(ch)
        self.logger.setLevel(lL)
	#self.logger.info("test")
        self.result=self.UNKNOWN

    def verifyThresholds(self,mode="minor"):
        ''' 
        in minor mode (default) success is when 
        check's result is below a certain threshhold.
        in major mode, success is when check's results have to
        be greater than given threshold
        '''
        if mode=="minor":
            if self.warningThreshold >= self.criticalThreshold:
                logging.error("FATAL: Violating thresholds (minor) criteria, warning threshold (%.1f) is greater than or equal to critical threshold(%.1f)\n" %(self.warningThreshold, self.criticalThreshold))
                sys.exit(self.UNKNOWN)
            else:
                logging.debug(("DEBUG: Warning threshold (%.1f) is minor than Critical threshold(%.1f)\n" %(self.warningThreshold, self.criticalThreshold)))
        elif mode=="major":
            if self.warningThreshold <= self.criticalThreshold:
                logging.error("FATAL: Violating thresholds (major) criteria, warning threshold (%.1f) is smaller than or equal to critical threshold(%.1f)\n" %(self.warningThreshold, self.criticalThreshold))
                sys.exit(self.UNKNOWN)
            else:
                logging.debug(("DEBUG: Warning threshold (%.1f) is major than Critical threshold(%.1f)\n" %(self.warningThreshold, self.criticalThreshold)))

    def getResult(self):
        return self.result

    def getOutMessage(self):
        return self.outMsg

    @abc.abstractmethod    
    def getInputParameters(self,argV):
        "get input parameters, each test has to define its own"

    @abc.abstractmethod
    def runCheck(self):
        "each test define its own check"

class NagiosTimeout(object):
    """Timeout class using ALARM signal"""
    class Timeout(Exception): pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0) # disable alarm

    def raise_timeout(self, *args):
        raise NagiosTimeout.Timeout()

