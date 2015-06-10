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

>
>define command { 

>       command_name  check_etokenserver
>	command_line  $USER2$/NagiosCheckeTokenServer.py
>	-u /usr/local/nagios/var/check_sandbox/check_etokenserver/etokenserverurls.txt
>	-o /usr/local/nagios/share/results/etokenserver.txt 
>	-w 10 -c 20

>}
					 
### OAR Login
### Virtuoso



