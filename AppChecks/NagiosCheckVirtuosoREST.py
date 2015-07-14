#!/usr/bin/python
import os
import sys
import getopt
import logging
import urllib2
import json
from NagiosCheck import NagiosCheck, NagiosTimeout


class NagiosCheckVirtuosoREST(NagiosCheck):

    def __init__(self, wT, cT, oF, k, l, e, lL=logging.DEBUG):
        NagiosCheck.__init__(self, wT, cT, oF, lL)
        self.keyword = k
        self.limit = l
        self.endpoint = e

    @classmethod
    def getInputParameters(self, argV=sys.argv):
        """implements the abstract method for the input retrieval"""

        inputDict = {}

        try:
            opts, args = getopt.getopt(argV[1:], "hk:l:e:o:c:w:",
                            ["--help", "--keyword", "--limit", "--endpoint",
                             "--outputfile", "--critical", "--warning"])
        except getopt.GetoptError:
            print argV[0] + '-k keyword -l limit -e endpoint -o outputfile'
            sys.exit(NagiosCheck.UNKNOWN)

        for opt, arg in opts:

            if opt == '-h':
                print ("-k keyword -e endpoint -l limit -o outputfile"
                      "-c critical_threshold -w warning_threshold") % (argV[0])
                print ("Number of keyword is limited to one."
                       "Offset is not supported, and forced to 0")
                sys.exit(NagiosCheck.UNKNOWN)
            elif opt in ("-k", "--keyword"):
                inputDict['keyword'] = arg
                #print keyword
            elif opt in ("-l", "--limit"):
                inputDict['limit'] = int(arg)
                #print keyword
            elif opt in ("-e", "--endpoint"):
                inputDict['endpoint'] = arg
                #print endpoint
            elif opt in ("-o", "--outputfile"):
                inputDict['outputFile'] = arg
            elif opt in ("-c", "--critical"):
                crit = arg
                inputDict['criticalThreshold'] = int(crit)
            elif opt in ("-w", "--warning"):
                warn = arg
                inputDict['warningThreshold'] = int(warn)

        return inputDict

    def validateLimit(self):

        '''Limit is the max number of records that the query can return.
        To be coherent with check, limit needs to be above warning threshold
        '''

        if self.limit < self.criticalThreshold:
            self.logger.error("Limit(%d) is below critical threshold,"
                              " which means that max number of records"
                              " returned would raise a critical status "
                              "for the check\n Reconsider thresholds and "
                              "limit parameters for the check." % (self.limit))
            sys.exit(NagiosCheck.UNKNOWN)
        elif self.limit < self.warningThreshold:
            self.logger.error("Limit (%d) is below warning threshold, "
                              "which means that max number of records"
                              " returned would raise a warning status"
                              " for the check\n Reconsider thresholds and "
                              "limit parameters for the check." % (self.limit))
            sys.exit(NagiosCheck.UNKNOWN)
        else:
            self.logger.info("Limit (%d) is above warning threshold, max"
                             " number of results expected is coherent with "
                             "the given thresholds " % (self.limit))

    def runCheck(self):

        queryTimeout = 15
        restURL = ("%s?keyword=%s&limit=%d&offset=0"
                   % (self.endpoint, self.keyword, self.limit))
        self.logger.info("Performing check on endpoint\n %s" % (restURL))

        try:
            with NagiosTimeout(queryTimeout):
                result = urllib2.urlopen(restURL)
                answer = result.read()
                json_object = json.loads(answer)
        except NagiosTimeout.Timeout:
            self.logger.error("%s exceeds %d seconds timeout !"
                               % (restURL, queryTimeout))
            return -1
        except Exception, err:
            self.logger.error("Impossible to perform check on this url %s\n %s"
                              % (restURL, err))
            return -1

        #e' una count, dovrebbe contenere sempre una sola riga
        #numRes=result['results']['bindings'][0]['callret-0']['value']
        #print numRes
        NumRes = len(json_object['simpleResources'])
        return NumRes


if __name__ == "__main__":

    inputDictionary = NagiosCheckVirtuosoREST.getInputParameters()

    check = NagiosCheckVirtuosoREST(inputDictionary['warningThreshold'],
                              inputDictionary['criticalThreshold'],
                              inputDictionary['outputFile'],
                              inputDictionary['keyword'],
                              inputDictionary['limit'],
                              inputDictionary['endpoint'])

    check.verifyThresholds(mode="major")
    check.validateLimit()

    check.logger.info('Ready to start Virtuoso API REST check')
    check.logger.debug('Warning threshold is %d, Critical threshold %d'
                        % (check.warningThreshold, check.criticalThreshold))
    numRecord = check.runCheck()

    if numRecord == -1:
        check.outMsg = "Unable to retrieve correctly the number of records"
        check.logger.error(check.outMsg)
        check.result = NagiosCheck.UNKNOWN
    elif numRecord < check.criticalThreshold:
        check.outMsg = "CRITICAL : %d records have been found." % (numRecord)
        check.logger.warning(check.outMsg)
        check.result = NagiosCheck.CRITICAL
    elif (numRecord >= check.criticalThreshold and
          numRecord < check.warningThreshold):
        check.outMsg = "WARNING : %d records have been found" % (numRecord)
        check.logger.warning(check.outMsg)
        check.result = NagiosCheck.WARNING
    else:
        check.outMsg = "SUCCESS : %d records have been found" % (numRecord)
        check.logger.info(check.outMsg)
        check.result = NagiosCheck.OK

    #print check.getResult()
    print check.getOutMessage()
    sys.exit(check.result)
