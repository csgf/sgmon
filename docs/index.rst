=======================================
SG-MON - INSTALLATION AND CONFIGURATION
=======================================


About
-----
This document covers installation and configuration of SG-Mon. A brief
overview of SG-Mon is also provided.

Introduction to SG-Mon
-----

SG-Mon is a collection of python scripts, developed with the purpose of
monitoring availability and reliability of web services and portlets
running on Catania Science Gateway Framework. SG-Mon scripts are
intended as plugin for network monitoring tools : this guide covers
Nagios, but with minor modifications they can be adapted to Zabbix.
Currently, it is composed by the following modules :

-  SGApp : run test instances of a given Scientific Gateway application
-  eTokenServer : verify the eTokenserver instance are up and properly
   working
-  Open Access Repository Login : verify login to an Open Access
   Repository
-  Virtuoso : verify that Virtuoso store instances are up and properly
   responding to queries

Requirements
------------

-  A working installation of Nagios (v3 or above)
-  Java (v 1.7 or above)
-  Apache jMeter
-  Python v. 2.7 (2.6 should be working as well).

Depending on the checks being actually activated, there could be further
dependencies, which are generally mentioned in the preamble of each
probe.

Installation
------------

The easiest way to install SG-Mon is to clone this repository (or
download the ZIP archive). Copy the content of AppChecks folder in a
directory able to execute plugins
(eg. /usr/local/nagios/myplugins). Create the directory if needed. A
part from NagiosCheck.py, which exports some functions imported by
other modules, all the other SG-Mon modules are each other
indipendent; see Configuration section in order to find out how to
setup properly each of the modules.

Configuration
-------------

Conforming with Nagios good practices, all SG-Mon modules return 0 if
the service status is OK, 1 if WARNING and 2 if CRITICAL. In any case,
the module returns a message with the output of the metric used for the
probe.

SGApp
~~~~~

This module is the most complex within SGMon, handling two separate
interactions : the first with Apache jMeter, for the execution of a
portlet instance on a CSGF portal, and the second with a CSGF's User
Tracking Database, in order to check that the application has been
really submitted to CSGF Engine. It's worth noting that this module is
completely trasparent to the portlet being submitted, which is defined
by the jMeter input file (*.jmx*). Here a possible definition of the
Nagios command

::

    define command {

    command_name check_sg-hostname-seq
    command_line $USER2$/NagiosCheckSGApp.py --critical 75 --warning 25
    --outfile $_SERVICEWEBLOG$ --jmx $_SERVICEJMX$ 
    --jmx-log $_SERVICEJMXLOG$ --number-of-jobs 1 --utdb-param $_SERVICEDBCONNPARAMS$ 
    --utdb-classes-prefix $_SERVICELIBRARYPATH$         
    }

as can be seen, many inputs are actually defined as service macros.
Outfile is a log file for the check, which is eventually exposed by
Nagios as extra note. With --number-of-jobs (shortly -n) it can be
specified how many time to submit the request; in order to compute
critical and warning rates, will be counted number of successful
submissions over total submissions. Here two different service
definitions : some values are common across different service intance,
for instance path to User Tracking DB client lib, while others vary
slightly according with the actual service instance being monitored.

::

    define service{

    use         generic-service
    host_name   recasgateway.cloud.ba.infn.it
    service_description     Hostname Sequential
    check_interval          120
    notification_interval   240
    check_command           check_sg-hostname-seq
    servicegroups           Science Gateway Applications
    _WEBLOG         /usr/local/nagios/share/results/SG-RECAS-BA-hostname-seq.txt
    _JMX            /usr/local/nagios/myplugins/SG-App-Checks/jmx/SG-Bari-HostnameSeq.jmx
    _LIBRARYPATH    /usr/local/nagios/myplugins/SG-App-Checks/javalibs
    _DBCONNPARAMS   /usr/local/nagios/myplugins/SG-App-Checks/etc/SG-Bari-UsersTrackingDBClient.cfg
    _JMXLOG         /usr/local/nagios/myplugins/SG-App-Checks/logs/SG-Bari-HostnameSeq.txt
    notes_url    https://sg-mon.ct.infn.it/nagios/results/SG-RECAS-BA-hostname-seq.txt
    }


    define service{

    use                     generic-service
    host_name               sgw.africa-grid.org
    service_description     Hostname Sequential
    check_interval          120
    notification_interval   240
    check_command           check_sg-hostname-seq
    servicegroups           Science Gateway Applications
    _WEBLOG                 /usr/local/nagios/share/results/SG-AfricaGrid-hostname-seq.txt
    _JMX                    /usr/local/nagios/myplugins/SG-App-Checks/jmx/SG-AfricaGrid-HostnameSeq.jmx
    _LIBRARYPATH            /usr/local/nagios/myplugins/SG-App-Checks/javalibs
    _DBCONNPARAMS           /usr/local/nagios/myplugins/SG-App-Checks/etc/SG-AfricaGrid-UsersTrackingDBClient.cfg
    _JMXLOG                 /usr/local/nagios/myplugins/SG-App-Checks/logs/SG-AfricaGrid-HostnameSeq.txt
    notes_url               https://sg-mon.ct.infn.it/nagios/results/SG-AfricaGrid-hostname-seq.txt
    }

eTokenServer
~~~~~~~~~~~~

This module takes as input:

-  a list of eToken urls
-  file where to stream check's output
-  warning and critical thresholds, computed as rate of successes
   contacting given urls.

A possible way to define the command for Nagios:

::

    define command { 

    command_name  check_etokenserver
    command_line  $USER2$/NagiosCheckeTokenServer.py
    --urlsfile /usr/local/nagios/var/check_sandbox/check_etokenserver/etokenserverurls.txt
    --outputfile /usr/local/nagios/share/results/etokenserver.txt 
    --warning 10 --critical 20

    }

OAR Login
~~~~~~~~~

This module is used to simulate login to an Open Access Repository. In
order to simulate the interaction with the web site, it is used Apache
jMeter; login information, as username, password and endpoint are
inserted in the jmx file given in input to the module. The other input
parameters accepted by the module are

-  path to the output file (which is eventually exposed by Nagios
   supporting troubleshooting )
-  property file for jMeter
-  jMeter log file
-  size of the test (number of attempts)
-  critical and warning thresholds (expressed as a fraction of
   successful attempts over number of attempts)

The path to the jMeter binary, is set within the module to
*/usr/local/apache-jmeter-2.9/bin*, and can be changed replacing
assigning a value to *jMeterPrefix* variable in *runJMeter* call. Here
an example of the Nagios command for this check:

::

    define command {

    command_name check_oar-login
    command_line $USER2$/NagiosCheckOARLogin.py 
    --critical 50 --warning 25 
    --outfile $_SERVICEWEBLOG$ 
    --jmx $_SERVICEJMX$ 
    --jmx-log $_SERVICEJMXLOG$ 
    --number-of-users 2             
    }

in this case, several parameters are defined as service macros:

::

    define service{

        use generic-service
        host_name  www.openaccessrepository.it
        service_description     Login
        check_interval          15
        notification_interval   240
        check_command        check_oar-login
        servicegroups           Semantic and Open Data
        _WEBLOG           /usr/local/nagios/share/results/openaccessrepository-login.txt
        _JMX              /usr/local/nagios/myplugins/OpenAccessRepo/jmx/openaccessrepo-login.jmx
        _JMXLOG           /usr/local/nagios/myplugins/OpenAccessRepo/logs/openaccessrepo-login.log
        notes_url         https://sg-mon.ct.infn.it/nagios/results/openaccessrepository-login.txt
    }

Virtuoso
~~~~~~~~

Beside built-in plugins, two modules have been developed for Virtuoso,
checking service availability either submitting explictly a SPARQL
query, or contacting the REST interface with proper keyword parameters.
Endpoint change slightly

::

    define command {

    command_name  check_virtuoso_db
    command_line  $USER2$/NagiosCheckVirtuoso.py 
    --query      $_SERVICEQUERYCOUNT$ 
    --endpoint   $_SERVICEENDPOINT$ 
    --outputfile $_SERVICEWEBLOG$ 
    --warning 0 --critical 15000000

    }

    define command { 

    command_name  check_virtuoso_apiREST
    command_line  $USER2$/NagiosCheckVirtuosoREST.py
    --keyword $_SERVICEKEYWORD$ 
    --endpoint $_SERVICEENDPOINT$ 
    --outputfile $_SERVICEWEBLOG$ 
    --limit 10 
    --warning 5 
    --critical 0
    }

as with OAR, several parameters are defined as service macros

::

    define service{

    use   generic-service
    host_name  virtuoso
    service_description   Number of records in the semantic DB
    check_interval        10
    notification_interval 720
    check_command  check_virtuoso_db
    _QUERYCOUNT    "select count(?s) where  {?s rdf:type <http://semanticweb.org/ontologies/2013/2/7/RepositoryOntology.owl#Resource>}"
    _ENDPOINT      "http://virtuoso.ct.infn.it:8896/chain-reds-kb/sparql"
    _WEBLOG        "/usr/local/nagios/share/results/virtuosoDB.txt"
    servicegroups  Semantic and Open Data
    }


    define service{

    use   generic-service
    host_name virtuoso
    service_description    API REST functionality
    check_interval         10
    notification_interval  720
    check_command check_virtuoso_apiREST
    _KEYWORD      "eye"
    _ENDPOINT     "http://www.chain-project.eu/virtuoso/api/simpleResources"
    _WEBLOG       /usr/local/nagios/share/results/virtuosoAPI.txt
    notes_url     https://sg-mon.ct.infn.it/nagios/results/virtuosoAPI.txt
    servicegroups Semantic and Open Data
    }

