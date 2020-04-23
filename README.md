# Call Link Uganda. The Ugandan Academy Interactive Voice Response -IVR

Call Link Uganda is a project inspired by the need to have an Inhouse IVR solutions to handle
the current volume of calls made by the **Call for Life project**.

This guide is essentially to help you get started with setting up IVR for either development or production environment

Table of Contents
=================
   * [Setting up your GitLab SSH](#setting-up-your-gitlab-ssh)
   * [Prerequisites](#prerequisites)
   * [Installation](#installation)
   * [Development](#development)
   * [References](#references)

Setting up your GitLab SSH  
======
Please click [here](https://docs.gitlab.com/ee/ssh/#rsa-ssh-keys) to follow the steps needed to set up your gitlab ssh key

Prerequisites
=============
Hardware Requirements
| Hardware | Suggested | Comment |
| ------ | ------ | ----- |
| SIP Phone | Fanvil, Grandstream, Yealink | This may not be need in case you have a soft phone on your pc or mobile phone |

Compute Requirements
| Component | Minimum Required | Comment |
| ------ | ------ |------|
| CPU | 2 cores | 1.6Ghz per core |
| RAM | 2 Gb | |
| Disk | 50 Gb | Solid State Drive prefered | 
Please note that these requirements maybe provisioned to a virtual machine (**Hyper V, VMware, Oracle Virtualbox, Citrix etc**)

Software  Requirements
| Software | Version | Reference | Comment |
| ------ | ------ |------| ------ |
| Ubuntu Server OS | 18.04 or higher | [Download from here](https://ubuntu.com/download/server) |
| MOTECH | 9.3 or higher | [Installation Instructions](http://gitlab.theacademy.co.ug/theacademy/scripts) | This is to be installed on the ubuntu server os mentioned in the first row of the table |
| Asterisk | 16 or higher | [Installation Instructions](https://computingforgeeks.com/how-to-install-asterisk-16-lts-on-ubuntu-18-04-16-04-debian-9/) | This is to be installed on the ubuntu server os mentioned in the first row of the table |

Installation
============
The initial thing to do before you run anything is to make sure your in the root directory of the application.

To start the installation, make sure have elevated privileges (**sudo**). Please run the following command in the terminal to gain elevated privileges.

**Note.** You will most likely be asked to enter a password after running the command depending on your system setup
```bash
$ sudo su
# 
```

When the dollar sign **$** changes to a hash **#**, means the command was successful and we are ready to go.

1. First step
    `config.ini.test`
    This is a demo file created as an example to how the config.ini file should look like.
    This file contains the format that should be followed when creating the config.ini file.
    This format should be followed correctly and the variables filled in accordingly.
    This file was created to ensure that this project can easily be run on different system setups with easy integration.

    This file must be created by the user as shown in the command below. In this file, the user can specify configurations like:
    - IP of the MOTECH host
    - AMI Configurations, needed by `app.py`
    - The audio directory path
    
    Well here is the command to create the config file
    
    ```bash
    # cp config.ini.test config.ini
    ```
    After creating the config file, you can edit the file with any of your favorite editors depending on your system setup i.e `nano`, `vim`, `gedit` etc.
    
    For example to use nano, run the following command.
    ```bash
    # nano config.ini
    ```

2. Second step

    The will help to install the application dependencies with the following command
    ```bash
    # bash install.sh
    ```
    This will take a couple of minutes but its worth it.
    
3. Third step

    Run the following command to setup your asterisk configuration (dialplan, sip configuration, asterisk manager etc)
    
    ```bash
    # bash asterisk.sh
    ```
    
4. Last step
    
    Configure your SIP phone / Soft phone
    Below are the following default details to be used while configuring the phone
    | Key | Value |
    | ------ | ------ |
    | username, auth name, etc | `200` |
    | password | `1234` |
    | host / IP Address | This should be IP of the machine running the application. It will vary on different machines and networks.  Run `ifconfig` in the ubuntu terminal to get the correct IP address. For example it could be like `192.168.8.50`. |

    After successfull configuration, make a call to `100` from your SIP or Soft phone and you should be able to connect to the IVR.
    
Development
===========
**Prerequisites**
Intermediate `Unix\Linux` Knowledge
A good understanding of `python3`, object oriented programing, package managers etc.
A good understanfing of `VoIP` (Voice over IP) mostly asterisk
A good understanfing of `MOTECH`. The applications which sends call requests to the IVR
An IDE for example `pycharm professional`

Some other things you find out yourself when everything almost failing for you ;)

**Ports used by the IVR while running**
Port: `5000`
This is where external applications like MOTECH which want to make calls through the IVR send call requests.
The Flask web server is the one which runs on this port by default.
Check the references below to find out more about Flask library

**Coding style**
We use the Python Enhancement Proposal (PEP) 8 style while coding. You can refer to this page [here](https://www.python.org/dev/peps/pep-0008/) for more info about the coding style.

Before pushing code to the respository, please check for any coding style errors with the following command
```bash
$ flake8 --max-line-length=120 --statistics ./app.py ./agi.py ./src
```

The output of this command with show you filenames with errors or nothing if there are no errors.

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
This is the library we use to parse Voice XML (VXML)

Flask [Reference](https://flask.palletsprojects.com/en/1.1.x/)
This is the library we use to develop the IVR API
