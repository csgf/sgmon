#!/usr/bin/python

import sys,logging,pycurl,getopt,string,cStringIO,OpenSSL.crypto

from datetime import datetime
from NagiosCheck import NagiosCheck, NagiosTimeout

class NagiosCheckeTokenServer(NagiosCheck):

    def __init__(self,wT,cT,oF,lL=logging.DEBUG):
        NagiosCheck.__init__(self,wT,cT,oF,logging.ERROR)
        self.eTokenUrls=[]
        self.score=0.0
        self.failures=0

    @classmethod
    def getInputParameters(self,argV=sys.argv):

        inputDict={}

        try:
            opts,args = getopt.getopt(argV[1:],"hu:o:c:w:",["--help","--urlsfile","--outputfile","--critical","--warning"])
        except getopt.GetoptError:
            print argV[0]+' -u <url file list> -o <outputfile> -w warning_threshold -c critical_threshold '
            sys.exit(NagiosCheck.UNKNOWN)

        for opt,arg in opts:
            if opt == '-h':
                print argV[0]+' -u <url file list> -o <outputfile> -w warning_threshold -c critical_threshold '
                sys.exit(NagiosCheck.UNKNOWN)
            elif opt in ("-u", "--urlsfile"):
                inputDict['eTokenURLsFile']=arg
                #print arg
            elif opt in ("-o", "--outputfile"):
                inputDict['outputFile']=arg
                #print outputFile	
            elif opt in ("-c","--critical"):
                crit=arg
                inputDict['criticalThreshold']=float(crit)/100.0
            elif opt in ("-w","--warning"):
                warn=arg
                inputDict['warningThreshold']=float(warn)/100.0

        return inputDict

    def runCheck(self):

        lineCounter=0

        for url in self.eTokenURLs:
            self.failures+=self.getProxy(url)
            lineCounter+=1

        self.score=float(self.failures)/lineCounter

        if self.score >= self.criticalThreshold:
            self.outMsg="eTokenServer CRITICAL: failed to retrieve proxy for %d targets out of %d given (%.2f %% failed)" %(self.failures,lineCounter,self.score*100)
            self.result=NagiosCheck.CRITICAL
        elif self.score >= self.warningThreshold:
            self.outMsg="eTokenServer WARNING: failed to retrieve proxy for %d targets out of %d given (%.2f %% failed)" %(self.failures,lineCounter,self.score*100)
            self.result=NagiosCheck.WARNING
        elif self.score >= 0.0:
            self.outMsg="eTokenServer OK: %d proxies retrieved out of %d given (%.2f %% failed)." %(lineCounter-self.failures,lineCounter,self.score*100)
            self.result=NagiosCheck.OK
        else:
            self.outMsg="eTokenServer status UNKNOWN: Unable to get eTokenServer health"
            self.result=NagiosCheck.UNKNOWN

        check.logger.info(self.outMsg)

    def getProxy(self,url):

        myTimeout=10
        buff = cStringIO.StringIO()

        check.logger.debug("attempting %s" %(url))
        #print "attempting %s\n" %(url)
        proxyTarget=pycurl.Curl()
        proxyTarget.setopt(proxyTarget.SSL_VERIFYPEER,0)
        proxyTarget.setopt(proxyTarget.URL,url.rstrip('\n'))
        proxyTarget.setopt(proxyTarget.WRITEFUNCTION, buff.write)
     
        try:
            with NagiosTimeout(myTimeout):
                proxyTarget.perform()
        except NagiosTimeout.Timeout:
            check.logger.error("%s exceeds %d seconds timeout !\n--------\n" %(url,myTimeout))
            return 1
        except pycurl.error as e:
            check.logger.error("%s has failed download (pycurl %s) !\n--------\n" %(url,e))
            return 1

        
        #now openssl checks 
        buff2string=buff.getvalue()

        try:
            cert=OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,buff2string)
        except OpenSSL.crypto.Error:
            check.logger.error("unable to read certificate downloaded from %s\n--------\n" %(url))
            return 1

        certCN=cert.get_subject().commonName
        dateASN=cert.get_notAfter()

        dateString="%s-%s-%s %s:%s:%s UTC" %(dateASN[0:4],dateASN[4:6],dateASN[6:8],dateASN[8:10],dateASN[10:12],dateASN[12:14])

        check.logger.debug("got a certificate for %s, valid until %s" %(certCN,dateString))
        #maybe check validity ?
        return 0

##############################################################3

if __name__ == "__main__":

    inputDictionary=NagiosCheckeTokenServer.getInputParameters()
    check=NagiosCheckeTokenServer(inputDictionary['warningThreshold'], 
                                  inputDictionary['criticalThreshold'],
                                  inputDictionary['outputFile'])

    check.logger.info('****************************************************************************************************')
    check.logger.debug('Starting test with warning threshold %f critical threshold %f' %(check.warningThreshold,check.criticalThreshold))
    check.logger.info(('Trying to fetch urls list from file %s\n' %(inputDictionary['eTokenURLsFile'])))

    try:
        check.eTokenURLs=open(inputDictionary['eTokenURLsFile'],'r')
    except IOError:
        check.logger.error("Unable to read urls from input file %s" %(inputDictionary['eTokenURLsFile']))
        check.logger.error("Unable to continue")
        sys.exit(NagiosCheck.UNKNOWN)

    check.logger.debug('fetch successful: ready to start test')
    check.runCheck()
    print check.outMsg
    sys.exit(check.result)
