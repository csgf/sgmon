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
directory able to execute plugins
(eg. /usr/local/nagios/myplugins). As SG-Mon modules are each other
indipendent, see Configuration section in order to find out how to
setup properly each of the module.  
  
## Configuration

### SGApp
### eTokenServer
### OAR Login
### Virtuoso



