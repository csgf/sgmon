#!/usr/bin/python
import os,sys,getopt,logging
from SPARQLWrapper import SPARQLWrapper,JSON
from NagiosCheck import NagiosCheck,NagiosTimeout 

class NagiosCheckVirtuoso(NagiosCheck):

    def __init__(self,wT,cT,oF,q,e,lL=logging.DEBUG):
        NagiosCheck.__init__(self,wT,cT,oF,lL)
        self.query=q
        self.endpoint=e
        
    @classmethod
    def getInputParameters(self,argV=sys.argv):
        "implements the abstract method for the input retrieval"

        inputDict={}

        try:
            opts,args = getopt.getopt(argV[1:],"hq:e:o:c:w:",["--help","--query","--endpoint","--outputfile","--critical","--warning"])
        except getopt.GetoptError:
            print argV[0]+'-q <query> -e <endpoint> -o <outputfile>'
            sys.exit(NagiosCheck.UNKNOWN)

        for opt,arg in opts:

            if opt == '-h':
                print argV[0]+"-q query -e endpoint -o outputfile -c critical_threshold -w warning_threshold"
                sys.exit(NagiosCheck.UNKNOWN)
            elif opt in ("-q", "--query"):
                inputDict['query']=arg
                #print query
            elif opt in ("-e", "--endpoint"):
                inputDict['endpoint']=arg
	        #print endpoint
            elif opt in ("-o", "--outputfile"):
                inputDict['outputFile']=arg
	        #print outputFile	
            elif opt in ("-c","--critical"):
                crit=arg
                inputDict['criticalThreshold']=int(crit)
            elif opt in ("-w","--warning"):
                warn=arg
                inputDict['warningThreshold']=int(warn)

        return inputDict

    def runCheck(self):

        queryTimeout=15
        sparql = SPARQLWrapper(self.endpoint)

        sparql.setQuery(self.query)
        sparql.setReturnFormat(JSON)

        self.logger.info("Performing query \n %s \n on endpoint\n %s" %(self.query,self.endpoint))

        try:
            with NagiosTimeout(queryTimeout):
                result = sparql.query().convert()
        except NagiosTimeout.Timeout:
            self.logger.error("Endpoint %s exceeds %d seconds timeout !" %(queryTimeout,self.endpoint))
            return -1
        except Exception, err:
            self.logger.error("Impossible to perform given query: %s\n on endpoint %s\n %s" %(self.query,self.endpoint,err))
            return -1

        #e' una count, dovrebbe contenere sempre una sola riga
        numRes=result['results']['bindings'][0]['callret-0']['value']
        #print numRes
        return int(numRes)    


if __name__ == "__main__":
    
    inputDictionary=NagiosCheckVirtuoso.getInputParameters()
    #for k,v in inputDictionary.iteritems():
    #    print "%s = %s\n" %(k,v)
    check=NagiosCheckVirtuoso(inputDictionary['warningThreshold'],
                              inputDictionary['criticalThreshold'],
                              inputDictionary['outputFile'],
                              inputDictionary['query'],
                              inputDictionary['endpoint'])
 
    check.verifyThresholds()
    check.logger.info('Ready to start Virtuoso DB check')
    check.logger.debug('Warning threshold is %d, Critical threshold %d' %(check.warningThreshold, check.criticalThreshold))
    numRecord=check.runCheck()

    if numRecord == -1:
        check.outMsg="Unable to retrieve correctly the number of records"
        check.logger.error(check.outMsg)
        check.result=NagiosCheck.UNKNOWN
    elif numRecord > check.criticalThreshold:
        check.outMsg="SUCCESS : %d records have been found." %(numRecord)
        check.logger.info(check.outMsg)
        check.result=NagiosCheck.OK
    elif (numRecord <= check.criticalThreshold and numRecord > check.warningThreshold):
        check.outMsg="WARNING : %d records have been found" %(numRecord)
        check.logger.warning(check.outMsg)
        check.result=NagiosCheck.WARNING
    else:
        check.outMsg="CRITICAL : %d records have been found" %(numRecord)
        check.logger.warning(check.outMsg)
        check.result=NagiosCheck.CRITICAL

    #print check.getResult()
    print check.getOutMessage()
    sys.exit(check.result)
