# SG-Mon
## About

SG-Mon is a collection of python scripts, developed with the purpose of
monitoring availability and reliability of web services and portlets
running on Catania Science Gateway Framework. 
SG-Mon scripts are intended as plugin for network monitoring tools :
this guide covers Nagios, but with minor modifications they can be adapted to Zabbix.
Currently, it is composed by the following modules : 

- SGApp : run test instances of a given Scientific Gateway application
- eTokenServer : verify the eTokenserver instance are up and properly working 
- Open Access Repository Login : verify login to an Open Access Repository
- Virtuoso : verify that Virtuoso store instances are up and properly responding to queries


## Requirements

* A working installation of Nagios (v3 or above)
* Java (v 1.7 or above) 
* Apache jMeter
* Python v. 2.7 (2.6 should be working as well).

Depending on the checks being actually activated, there could be
further dependencies, which are generally mentioned in the preamble of each probe. 

## Installation

The easiest way to install SG-Mon is to clone this repository (or
download the ZIP archive). Copy the content of AppChecks folder in a
directory able to execute plugins (eg. /usr/local/nagios/myplugins). A
part from NagiosCheck.py, which exports some functions imported by
other modules, all the other SG-Mon modules are each other
indipendent; see Configuration section in order to find out how to
setup properly each of the modules.
  
## Configuration

Conformly with the Nagios good practices, all SG-Mon modules return 0
if the service status is OK, 1 if WARNING and 2 if CRITICAL. In any
case, the module returns a message with the output of the metric used
for the probe.

### SGApp
### eTokenServer
This module takes as input:

- a list of eToken urls
- file where to stream check's output  
- warning and critical thresholds, which represents here rate of
failures contacting given urls. 
This is a possible way to define the command for Nagios

```define command { 

   command_name  check_etokenserver
   command_line  $USER2$/NagiosCheckeTokenServer.py
	-u /usr/local/nagios/var/check_sandbox/check_etokenserver/etokenserverurls.txt
	-o /usr/local/nagios/share/results/etokenserver.txt 
	-w 10 -c 20

}
```
					 
### OAR Login

This module is used to simulate login to an Open Access
Repository. In order to simulate the interaction with the web site, it
is used Apache jMeter; login information, as username, password and
endpoint are inserted in the jmx file given in input to the
module. The other input parameters accepted by the module are 

- path to the output file (which is eventually exposed by Nagios
  supporting troubleshooting ) 
- property file for jMeter 
- jMeter log file
- size of the test (number of attempts)
- critical and warning thresholds (expressed as a fraction of
  successful attempts over number of attempts)  
  
The path to the jMeter binary, is set within the module to
_/usr/local/apache-jmeter-2.9/bin_, and can be changed replacing
assigning a value to _jMeterPrefix_ variable in _runJMeter_ call. 
Here an example of the Nagios command for this check: 
```
define command {

   command_name check_oar-login
   command_line $USER2$/NagiosCheckOARLogin.py 
   -c 50 -w 25 
   -o $_SERVICEWEBLOG$ 
   -j $_SERVICEJMX$ 
   -l $_SERVICEJMXLOG$ 
   -n 2				
}
```
in this case, several parameters are defined as service macros: 

```
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
```

### Virtuoso



