#!/usr/bin/python

import sys,subprocess,os,logging,getopt,time
import tempfile
from datetime import datetime
from NagiosCheck import NagiosCheck, NagiosTimeout

class NagiosCheckApp(NagiosCheck):

    def __init__(self,warnThr,critThres,outFil,jmxDF,jmxLF,testSz,utdbCParFile,utdbCClassPre,logLev=logging.DEBUG):

        NagiosCheck.__init__(self,warnThr,critThres,outFil,logLev)
        ## get specific input
        self.jmxDescFile=jmxDF
        self.jmxLogFile=jmxLF
        self.jobDescriptions=[]
        self.testSize=testSz
        self.UTDbClParamFile=utdbCParFile
        self.UTDbCLClassPrefix=utdbCClassPre

    @classmethod
    def getInputParameters(self,argV=sys.argv):
        "implements the abstract method for the input retrieval"

        inputDict={}
        filename=argV[0]
        helpMessage="""%s -c <critical_threshold_rate> -w <warning_threshold_rate> -o <output_file>-j <jmx_properties_file> -l <jmx_log_file> -n <number of jobs> -p <user tracking db connection parameters> -t <utdb-classes-prefix>""" %(filename)

        try:
            opts,args=getopt.getopt(argV[1:],"hc:w:o:j:l:n:p:t:",["--help","--critical","--warning","--outfile","--jmx","--jmx-log","--number-of-jobs","--utdb-param","--utdb-classes-prefix"])
        except getopt.GetoptError:
            print helpMessage
            sys.exit(NagiosCheck.UNKNOWN)

        for opt,arg in opts:
            if opt == '-h':
                print helpMessage
                sys.exit(NagiosCheck.UNKNOWN)
            elif opt in ("-c", "--critical"):
                inputDict['criticalThreshold']=float(arg)/100.0
            elif opt in ("-w", "--warning"):
                inputDict['warningThreshold']=float(arg)/100.0
            elif opt in ("-o", "--outfile"):
                inputDict['logFile']=arg
            elif opt in ("-j", "--jmx"):
                inputDict['jmxF']=arg
            elif opt in ("-l", "--jmx-log"):
                inputDict['jmxL']=arg
            elif opt in ("-n","--number-of-jobs"):
                inputDict['testSize']=int(arg)
            elif opt in ("-p","--utdb-param"):
                inputDict['utdbClParam']=arg
            elif opt in ("-t","--utdb-classes-prefix"):
                inputDict['utdbClClassPre']=arg

        return inputDict

    def runJMeter(self,jMeterPrefix="/usr/local/apache-jmeter-2.9/bin"):
        """ perform a single jmeter run """
        
        jMeterOutcome=0
        jobDesc="SG-MonCheck-JM_%s" %(datetime.now().strftime("%Y%m%d-%H%M%S"))
        mytmp=tempfile.TemporaryFile(mode='w+b',dir='/tmp',suffix='jmeterDEBUG')
        #shutup=os.open('/tmp/jmeterdebug.txt','w')
        os.chdir('/tmp')
        jMeterCmd="%s/jmeter -n -t %s -l %s -JjobDes=%s" %(jMeterPrefix,self.jmxDescFile,self.jmxLogFile,jobDesc)
	# sembra che a nagios dia fastidio la verbosita'

        ### self.logger.debug(jMeterCmd.split())
        self.logger.debug("Starting jMeter with command: %s " %(jMeterCmd))
        # subprocess wants a list, where first element is command name, and others (optional) arguments
      
        try:
            jMeterOutcome=subprocess.call(jMeterCmd.split(),stdout=mytmp,stderr=mytmp)
            # WORKS 
            #jMeterOutcome=subprocess.Popen(jMeterCmd.split(),stdout=mytmp,stderr=mytmp)
            self.logger.debug("jMeter executed for %s" %(jobDesc))
        except subprocess.CalledProcessError as e:
            self.logger.error("%s : could not call jmeter" %(str(e)))
            return 1
        except Exception as e:
            self.logger.error("%s : could not call jmeter" %(str(e)))
            return 1

        if (jMeterOutcome != ""):
            #self.logger.debug(jMeterOutcome)
            self.logger.info("job %s submitted: job description is %s" %(self.jmxDescFile,jobDesc))
            # job description list will contain only submitted jobs descriptors
            self.jobDescriptions.append(jobDesc)
            return 0
        else:
            self.logger.error("Some error occurred during %s submission" %(self.jmxDescFile))
            return 1

    def setUTDBJavaContext(self):

        javapath="%s/log4j-1.2-1.2.16.jar:%s/jsaga-job-management-1.5.8.jar:%s/mysql.jar:%s" %(self.UTDbCLClassPrefix,self.UTDbCLClassPrefix,self.UTDbCLClassPrefix,self.UTDbCLClassPrefix)
        os.environ['CLASSPATH']=javapath

    def checkJobOutcome(self,jobDescr):
        # run UTDB Client

        """ Users tracking DB Client returns back a integer """
        """ this tuple maps back the job status code with the corresponding label """
        jobStatus="DONE","NEW","SUBMITTED","RUNNING","SUSPENDED","FAILED","CANCELED","Not Found","Unknown"
            
        self.logger.debug("Querying User Tracking Database about %s" %(jobDescr))
        utdbResponse=subprocess.call(["java", "UsersTrackingDBClient",self.UTDbClParamFile,jobDescr])

        if (utdbResponse < 7):
            self.logger.info("%s found in User Tracking Database with status : %s" %(jobDescr, jobStatus[utdbResponse]))
            return 0
        else:
            self.logger.info("%s not found in User Tracking Database" %(jobDescr))
            return 1

    def runCheck(self):

        # runJmeter gives 0 on success, 1 on failure
        # mettere timeout ??
        submitted=0
        missed=0
        failures=0
        testResults={}

        """ call runJMeter  """
        for c in range(0,self.testSize):
            self.logger.debug("Calling jmeter for job %d" %(c))
            missed += self.runJMeter()
        
        submitted=self.testSize - missed

        # if there are no jobs submitted there's nothing to check further
        if submitted <= 0:
            testResults['score']=1
            return

        pause=6*submitted
        
        # take a break - allow the Grid Engine to register the job
        self.logger.debug("Sleeping a bit, giving some time to Grid Engine for jobs registration (6 second for each job)")
        time.sleep(pause)
        
        self.setUTDBJavaContext()

        for jD in self.jobDescriptions:
            failures+=self.checkJobOutcome(jD)

        # allows check.testSize = 0 - just for debug, in which case score is 100%
        # if testSize is zero, then return failure code
        #score=(check.testSize != 0) and float(failures)/float(check.testSize) or 1
        score=float (failures)/float(check.testSize)
        
        testResults['score']=score
        testResults['failures']=failures
        testResults['submitted']=submitted

        return testResults


    def analyzeScore(self,checkScore,failures,submitted):

        if checkScore >= self.criticalThreshold:
            self.outMsg="CRITICAL: failed to retrieve status for %d jobs out of %d submitted (%.2f %% failed)" %(failures,submitted,checkScore*100)
            self.result=NagiosCheck.CRITICAL
        elif checkScore >= self.warningThreshold:
            self.outMsg="WARNING: failed to retrieve status for %d jobs out of %d submitted (%.2f %% failed)" %(failures,submitted,checkScore*100)
            self.result=NagiosCheck.WARNING
        elif checkScore >= 0.0:
            self.outMsg="OK: status retrieved for %d jobs out of %d submitted (%.2f %% failed)." %(submitted - failures,submitted,checkScore*100)
            self.result=NagiosCheck.OK
        else:
            self.outMsg="UNKNOWN: Unable to check on service's health"
            self.result=NagiosCheck.UNKNOWN

        self.logger.info(self.outMsg)
        

if (__name__ == "__main__"):

    failures=0

    inputDict=NagiosCheckApp.getInputParameters()

    check=NagiosCheckApp(inputDict['warningThreshold'],
                                 inputDict['criticalThreshold'],
                                 inputDict['logFile'],
                                 inputDict['jmxF'],
                                 inputDict['jmxL'],
                                 inputDict['testSize'],
                                 inputDict['utdbClParam'],
                                 inputDict['utdbClClassPre']
                                 )
    check.verifyThresholds()

    check.logger.info("*******************************************************************************************************")
    check.logger.info("Input parameters taken, starting check with %d jobs. Critical Threshold %.2f Warning Threshold %.2f" %(check.testSize,check.criticalThreshold, check.warningThreshold)) 

    testResults=check.runCheck()
    check.analyzeScore(testResults['score'],testResults['failures'],testResults['submitted'])
    print check.outMsg
    sys.exit(check.result)
    
