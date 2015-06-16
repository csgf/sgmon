# SG-Mon
## About

SG-Mon is a collection of python scripts, developed with the purpose of
monitoring availability and reliability of web services and portlets/servlets
based on Catania Science Gateway Framework. 
SG-Mon scripts are intended as plugin for a network monitoring tool :
this guide covers Nagios, but with minor modifications SG-Mon can be adapted to Zabbix.
Currently, SG-Mon is composed by the following modules : 

- SGApp : it run test instances of a chosen Scientific Gateway application
- eTokenServer : verify the eTokenserver instances are up and properly working 
- Open Access Repository Login : verifies login to an Open Access Repository
- Virtuoso : verifies that Virtuoso store instances are up and properly responding to queries


## Requirements

* A working installation of Nagios (v3 or above)
* Java (v 1.7 or above) 
* Apache jMeter (v. 2.9)
* Python v. 2.7 (2.6 should be working as well).

Depending on the checks being actually activated, there could be
further dependencies, which are generally mentioned in the preamble of each probe. 

## Installation & Configuration

Checkout detailed instructions [here](https://github.com/csgf/sgmon "Installation and Configuration")

## Support 

If you need help or you need clarifications about SGMon, contact the [author](https://github.com/egiorgio "Author")
								   

