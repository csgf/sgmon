#!/usr/bin/python
import sys
import subprocess
import os
import logging
import getopt
import time
import tempfile
from datetime import datetime
from NagiosCheck import NagiosCheck, NagiosTimeout


class NagiosCheckApp(NagiosCheck):

    def __init__(self, warnThr, critThres, outFil, jmxDF,
                    jmxLF, testSz, logLev=logging.DEBUG):

        NagiosCheck.__init__(self, warnThr, critThres, outFil, logLev)
        ## get specific input
        self.jmxDescFile = jmxDF
        self.jmxLogFile = jmxLF
        self.testSize = testSz

    @classmethod
    def getInputParameters(self, argV=sys.argv):
        "implements the abstract method for the input retrieval"

        inputDict = {}
        filename = argV[0]
        helpMessage = ("%s -c <critical_threshold> -w <warning_threshold>"
                       "-o <output_file> -j <jmx_properties_file> "
                       "-l <jmx_log_file> -n <number of users>" % (filename))

        try:
            opts, args = getopt.getopt(argV[1:], "hc:w:o:j:l:n:",
                       ["--help", "--critical", "--warning",
                        "--outfile", "--jmx", "--jmx-log",
                        "--number-of-users"])

        except getopt.GetoptError:
            print helpMessage
            sys.exit(NagiosCheck.UNKNOWN)

        for opt, arg in opts:
            if opt == '-h':
                print helpMessage
                sys.exit(NagiosCheck.UNKNOWN)
            elif opt in ("-c", "--critical"):
                inputDict['criticalThreshold'] = float(arg) / 100.0
            elif opt in ("-w", "--warning"):
                inputDict['warningThreshold'] = float(arg) / 100.0
            elif opt in ("-o", "--outfile"):
                inputDict['logFile'] = arg
            elif opt in ("-j", "--jmx"):
                inputDict['jmxF'] = arg
            elif opt in ("-l", "--jmx-log"):
                inputDict['jmxL'] = arg
            elif opt in ("-n", "--number-of-users"):
                inputDict['testSize'] = int(arg)

        return inputDict

    def runJMeter(self, jMeterPrefix="/usr/local/apache-jmeter-2.9/bin"):
        """
        perform a single jmeter run (however more than one user is supported)
        """

        jMeterOutcome = 0
        jobDesc = ("SG-MonCheck-JM_%s"
                   % (datetime.now().strftime("%Y%m%d-%H%M%S")))

        mytmp = tempfile.TemporaryFile(mode='w+b',
                         dir='/tmp', suffix='jmeterDEBUG')

        jMeterCmd = ("%s/jmeter -n -t %s -l %s -JLoopSize=%s"
                      % (jMeterPrefix, self.jmxDescFile,
                         self.jmxLogFile, self.testSize))

        self.logger.debug("Starting jMeter with command: %s " % (jMeterCmd))

        # subprocess wants a list, where first element is command name
        # plus others (optional) arguments
        try:
            jMeterOutcome = subprocess.call(jMeterCmd.split(),
                                            stdout=mytmp, stderr=mytmp)
            # DEBUG MODE
            # jMeterOutcome=subprocess.check_output(jMeterCmd.split(),
            # stderr=subprocess.STDOUT)
            self.logger.debug("jMeter executed for %s" % (jobDesc))
        except subprocess.CalledProcessError as e:
            self.logger.error("%s : could not call jmeter" % (str(e)))
            return 1
        except Exception as e:
            self.logger.error("%s : could not call jmeter" % (str(e)))
            return 1

        if (jMeterOutcome != ""):
            self.logger.debug("jMeter  %s exit status is %d"
                              % (jobDesc, jMeterOutcome))
            # DEBUG MODE
            # self.logger.debug("jMeter  %s exit status is %s"
            # % (jobDesc,jMeterOutcome))
            return 0
        else:
            self.logger.error("Some error occurred during %s submission"
                              % (self.jmxDescFile))
            return 1

    def checkOutcome(self):
        """ Exit with success only if all
            rows in the html have access code 200 (OK) """
        import re
        results = open(self.jmxLogFile)
        error = ""
        finalResponse = 0
        userResponses = {}
        regexp = '\d+,\d+,([\w ]+),([\w ]+),[\w ]+,(oar-user \d-\d)'

        for line in results:
            check = re.match(regexp, line)
            if check:
                pageTitle = check.group(1)
                pageResponse = check.group(2)
                user = check.group(3)
                if pageResponse != "200":    # there was an error
                    userResponses[user] = 1
                    error += line
                    self.logger.error("Error accessing [%s]: %s"
                                      % (pageTitle, line[:-1]))
            else:  # regexp didn't match
                error += line
                self.logger.error("Error : %s" % (line[:-1]))

        results.close()

        for r in userResponses:
            if userResponses[r] == 1:		# there was an error, raise the flag
                finalResponse += 1

        return finalResponse

    def runCheck(self):

        # runJmeter gives 0 on success, 1 on failure

        submitted = 0
        missed = 0
        failures = 0
        testResults = {}

        """ call runJMeter  """
        #for c in range(0,self.testSize):
            #self.logger.debug("Calling jmeter for user %d" %(c+1))
        missed += self.runJMeter()
        submitted = self.testSize - missed

        # if there are no jobs submitted there's nothing to check further
        if submitted <= 0:
            testResults['score'] = 1
            return

        self.logger.debug("Login check performed")

        #for c in range(0,self.testSize):
        failures += self.checkOutcome()
        # allows check.testSize = 0 - just for debug,
        # in which case score is 100%
        # if testSize is zero, then return failure code
        # score=(check.testSize != 0)
        # and float(failures) / float(check.testSize) or 1
        score = float(failures) / float(check.testSize)

        testResults['score'] = score
        testResults['failures'] = failures
        testResults['submitted'] = submitted

        return testResults

    def analyzeScore(self, checkScore, failures, submitted):

        if checkScore >= self.criticalThreshold:
            self.outMsg = ("CRITICAL: failed to login for %d user%s out of %d"
                           " attempted (%.2f %% failed)"
                          % (failures, ({True: '', False: 's'}[submitted < 2]),
                           submitted, checkScore * 100))
            self.result = NagiosCheck.CRITICAL
        elif checkScore >= self.warningThreshold:
            self.outMsg = ("WARNING: failed to login for %d user%s out of %d"
                            " attempted (%.2f %% failed)"
                          % (failures, ({True: '', False: 's'}[submitted < 2]),
                            submitted, checkScore * 100))
            self.result = NagiosCheck.WARNING
        elif checkScore >= 0.0:
            self.outMsg = ("OK: login achieved for %d user%s out of %d"
                           " attempted (%.2f %% failed)"
                           % (submitted - failures,
                            ({True: '', False: 's'}[submitted < 2]),
                            submitted, checkScore * 100))
            self.result = NagiosCheck.OK
        else:
            self.outMsg = "UNKNOWN: Unable to check on service's health"
            self.result = NagiosCheck.UNKNOWN

        self.logger.info(self.outMsg)


if (__name__ == "__main__"):

    failures = 0

    inputDict = NagiosCheckApp.getInputParameters()

    check = NagiosCheckApp(inputDict['warningThreshold'],
                                 inputDict['criticalThreshold'],
                                 inputDict['logFile'],
                                 inputDict['jmxF'],
                                 inputDict['jmxL'],
                                 inputDict['testSize']
                                 )
    check.verifyThresholds()

    check.logger.info("*" * 80)
    check.logger.info(("Input parameters taken, starting check with %d jobs."
                       "Critical Threshold %.2f Warning Threshold %.2f"
                        % (check.testSize, check.criticalThreshold,
                           check.warningThreshold)))

    testResults = check.runCheck()
    check.analyzeScore(testResults['score'], testResults['failures'],
                       testResults['submitted'])
    print check.outMsg
    os.remove(check.jmxLogFile)
    sys.exit(check.result)
