# Call Link Uganda. The Ugandan Academy In-house Interactive Voice Response - IVR

>>>
Call Link Uganda is a project inspired by the need to have an In-house IVR solutions to handle
the current volume of calls made by the **Call for Life project**.

This guide is essentially to help you get started with setting up IVR for either development or production environment
>>>

Table of Contents
=================
   * [Setting up your GitLab SSH](#setting-up-your-gitlab-ssh)
   * [Prerequisites](#prerequisites)
   * [Installation](#installation)
   * [Development](#development)
   * [References](#references)

Setting up your GitLab SSH  
======
>>>
Please click [here](https://docs.gitlab.com/ee/ssh/#rsa-ssh-keys) to follow the steps needed to set up your gitlab ssh key
>>>

Prerequisites
=============
**Hardware Requirements**  

| Hardware | Suggested | Comment |
| ------ | ------ | ----- |
| SIP Phone | Fanvil, Grandstream, Yealink | This may not be need in case you have a soft phone on your pc or mobile phone |


**Compute Requirements**  

| Component | Minimum Required | Comment |
| ------ | ------ | ------ |
| CPU | 2 cores | 1.6Ghz per core |
| RAM | 2 Gb | |
| Disk | 50 Gb | Solid State Drive preferred |


Please note that these requirements maybe provisioned to a virtual machine (**Hyper V, VMware, Oracle Virtualbox, Citrix etc**)


**Software  Requirements**  

| Software | Version | Reference | Comment |
| ------ | ------ |------| ------ |
| Ubuntu Server OS | 18.04 or higher | [Download from here](https://ubuntu.com/download/server) |
| MOTECH | 9.3 or higher | [Installation Instructions](http://gitlab.theacademy.co.ug/theacademy/scripts) | This is to be installed on the ubuntu server os mentioned in the first row of the table |
| Asterisk | 16 or higher | [Installation Instructions](https://computingforgeeks.com/how-to-install-asterisk-16-lts-on-ubuntu-18-04-16-04-debian-9/) | This is to be installed on the ubuntu server os mentioned in the first row of the table |


Installation
============
The initial thing you need to do before running anything is to make sure your in the root directory of the application.  
Use the following command to change to the application root directory if not yet there.

```bash
$ cd /path/to/your/application/root/directory
```  

Please replace the above path with a correct path on your file system.  


**First step**  
We first deal with this file: `config.ini.test`  
>>>
This is a demo file created as an example to show how the config.ini file should look like.  
This file contains the format that should be followed when creating the config.ini file.  
This format should be followed correctly and the variables filled in accordingly.  
This file was created to ensure that this project can easily be run on different system setups with easy integration.  
>>>  

This file must be created by the user as shown in the command below. In this file, the user can specify configurations like:  
+ IP of the MOTECH host  
+ AMI Configurations, needed by `app.py`  
+ The audio directory path  
+ The trunk name if one is configured on the system  


Well here is the command to create the `config.ini` file out of its template `config.ini.test`

```bash
$ cp config.ini.test config.ini
```  

After creating the config file, you can edit the file with any of your favorite editors depending on your system setup i.e `nano`, `vim`, `gedit` etc.  

For example to use nano, run the following command.
```bash
$ nano config.ini
```


**Second step**  
The will help to install the application dependencies with the following command  
```bash
$ sudo bash install.sh
```  
This may take a while but it's worth it.


    
**Third step**  

Run the following command to setup your asterisk configuration (dialplan, sip configuration, asterisk manager etc)  

```sh
$ sudo bash asterisk.sh
```


**Last step**  
Configure your SIP phone / Soft phone  
Below are the default details to be used while configuring the phone  


| Key | Value |
| ------ | ------ |
| username, auth name, etc | `200` |
| password | `1234` |
| host / IP Address | This should be IP of the machine running the application.<br>It will vary on different machines and networks.<br>Run `ifconfig` in the ubuntu terminal to get the correct IP address.<br>For example it could be like `192.168.8.50`. |


After a successful configuration, make a call to `100` from your SIP or Soft phone, you should be able to connect to the IVR.


Development
===========
**Prerequisites**
>>>
Intermediate `Unix\Linux` Knowledge  
A good understanding of `python3`, object oriented programing, package managers etc.  
A good understanding of `VoIP` (Voice over IP) mostly asterisk 16    
A good understanding of `MOTECH`. The applications which sends call requests to the IVR  
An good IDE for example `pycharm professional`  
>>>


**Permissions Fixing**  
Use the following commands to fix the application permissions  
```bash
$ sudo chown -R asterisk:$USER /path/to/application/directory
```


**Ports used by the IVR while running**
>>>
Port: `5000`  
This is where external applications like MOTECH which want to make calls through the IVR send call requests.  
The Flask web server is the one which runs on this port by default.  
Check the references below to find out more about the Flask library.  
>>>


**Coding style**  
>>>
We use the Python Enhancement Proposal (PEP) 8 style while coding.  
You can refer to this page [here](https://www.python.org/dev/peps/pep-0008/) for more info about the coding style.  
>>>


Before pushing code to the repository, please check for any coding style errors with the following command otherwise your pipelines will fail  
```bash
$ flake8 --max-line-length=120 --statistics ./app.py ./agi.py ./src
```

The output of this command with show you filenames with errors or nothing if there ain't any.


To fix your coding style errors to match the coding style (PEP8) automatically, run the following command.
```bash
$ autopep8 --in-place --aggressive --aggressive <filename_with_errors or a directory>
```
Note. This tool may not fix some styling errors therefore there might be need for manual fixing.


References
==========

Asterisk Manager Interface (AMI) - [Reference](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=4817239)  
This is the interface we use to initiate calls and get call responses from asterisk


Asterisk Gateway Interface (AGI) [Reference](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589)  
This is the interface we use to manipulate the asterisk language after parsing VXML


Beautiful Soup [Reference](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)  
This is the library we use to parse Voice XML (VXML) from external applications like MOTECH


Flask [Reference](https://flask.palletsprojects.com/en/1.1.x/)  
This is the library we use to develop the IVR API


Flake8 [Reference](http://flake8.pycqa.org/en/latest/user/configuration.html)  
Used for code style linting (checking).

Autopep8 [Reference](https://pypi.org/project/autopep8/)  
Auto fixes code style errors
