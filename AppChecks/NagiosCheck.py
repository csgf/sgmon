#!/usr/bin/python
import abc
import logging
import sys
import signal
from logging.handlers import RotatingFileHandler


class NagiosCheck(object):
    "Base class for my Nagios plugins"
    __metaclass__ = abc.ABCMeta

    "Exit statuses"
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    def __init__(self, wT, cT, oF, lL=logging.DEBUG):
        """Get check thresholds and initialize service variables"""

        self.warningThreshold = wT
        self.criticalThreshold = cT

        self.outMsg = "Check not really started"
        self.logger = logging.getLogger("NagiosCheck")
        logHandler = RotatingFileHandler(oF, mode='a',
                                         maxBytes=19999,
                                         backupCount=7)

        logHandler.setFormatter(
            logging.Formatter('%(asctime)-4s %(levelname)-4s %(message)s')
            )
        self.logger.addHandler(logHandler)
        self.logger.setLevel(lL)
        # check result is initially UNKNOWN
        self.result = self.UNKNOWN

    def verifyThresholds(self, mode="minor"):
        """
        Verify that given thresholds are coherent with checks' logic.
        With minor mode (default), success is when
        result is BELOW a certain threshhold.
        In major mode, success is when check's results is
        ABOVE given threshold
        """

        if mode == "minor":
            if self.warningThreshold >= self.criticalThreshold:
                msg = ("FATAL - Threshold criteria violated. In minor mode "
                       "warning threshold (%.1f) can't be greater or equal"
                       "than critical threshold (%.1f) \n"
                       % (self.warningThreshold, self.criticalThreshold))
                logging.error(msg)
                sys.exit(self.UNKNOWN)
            else:
                msg = ("OK, minor mode and warning threshold (%.1f) is"
                       "smaller than critical threshold (%.1f) \n"
                       % (self.warningThreshold, self.criticalThreshold))
                logging.debug(msg)
        elif mode == "major":
            if self.warningThreshold <= self.criticalThreshold:
                msg = ("FATAL - Threshold criteria violated. In major mode "
                       "warning threshold (%.1f) can't be smaller or equal "
                       "than critical threshold (%.1f) \n"
                       % (self.warningThreshold, self.criticalThreshold))
                logging.error(msg)
                sys.exit(self.UNKNOWN)
            else:
                msg = ("OK, major mode and warning threshold (%.1f) is "
                       "greater than critical threshold (%.1f)\n"
                       % (self.warningThreshold, self.criticalThreshold))
                logging.debug(msg)

    def getResult(self):
        """Return probe result"""
        return self.result

    def getOutMessage(self):
        """Return probe output message"""
        return self.outMsg

    @abc.abstractmethod
    def getInputParameters(self, argV):
        """Get input parameters. Each test has to define its own"""

    @abc.abstractmethod
    def runCheck(self):
        """Each test define its own check"""


class NagiosTimeout(object):
    """Timeout class using ALARM signal"""
    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)     # disable alarm

    def raise_timeout(self, *args):
        raise NagiosTimeout.Timeout()
