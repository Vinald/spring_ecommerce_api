# Academy IVR  
Academy IVR is a project inspired by the need to have an In-house IVR solutions to handle
the current volume of calls made by the **Call for Life project**.  
This guide is essentially to help you get started with setting up IVR.  


Table of Contents
=================
   * [Prerequisites](#prerequisites)
   * [Local Installation](#local-installation)
   * [Docker Setup](#docker-setup)
   * [SIP Phone Configuration](#sip-phone-configuration)
   * [Coding Style](#coding-style)
   * [References](#references)


Prerequisites
=============
**VoIP Requirements**  
A softphone [Zoiper](https://www.zoiper.com/en/voip-softphone/download/current) or a physical SIP phone Fanvil, Grandstream, Yealink etc.  

**Compute Requirements**  

| CPU | RAM | Storage |
| ------ | ------ | ------ |
| 1 | 1gb | 20gb |  


**Software  Requirements**  

| Software | Version | Reference | Comment |
| ------ | ------ |------| ------ |
| Fresh Ubuntu Server OS | 20.04 or higher | [Download from here](https://ubuntu.com/download/server) |  


**Also make sure you have a working internet connection**  


Local Installation
==================
Easiest way to run the Academy IVR is by using the installation script as guided below  

```bash
$ git clone git@gitlab.theacademy.co.ug:theacademy/ivr.git
$ cd ivr
```  

Run this command only on the first install of the IVR.  
```bash
$ sudo python3 bin/install.py --env dev --deploy true --quiet false
```  

Please refer to `config.json` for the project configurations like `database credentials`, `asterisk logins` etc before you start the application.    

Start the `IVR API service` on port `5000` with the following command. API is accessable via `http://your-ip:5000`
```bash
$ sudo chown -R $USER:asterisk $(pwd) # Fix permissions before you start the application
$ python3 run.py
``` 

Edit the `.env.development` file under the `web` directory and replcace `172.18.0.1` with your actual IP address.
You can use the linux `nano` editor to do that if you know how to use it with the command below.  
```bash
$ nano ./web/.env.development
```  

Finally, start the `IVR Web Application` on port `8080` with the following commands. In your browser, use `http://your-ip:8080`
```bash
$ npm --prefix ./web run serve
```  



Docker Setup
==================
On initial setup, run the following commands  

```bash
$ git clone git@gitlab.theacademy.co.ug:theacademy/ivr.git
$ cd ivr
$ sudo apt update && sudo apt install docker.io docker-compose -y
$ docker-compose up -d --build
```

**Daily commands**  
To stop the containers when your done with development, run the following command.  
```bash
$ docker-compose stop
```

To resume your development, run the following command.  
```bash
$ docker-compose start
```  

After `docker-compose start`, you will be to access the `IVR API Service` via `http://your-ip:5000` and the `IVR Web App` via `http://your-ip:8000`  


SIP Phone Configuration  
=======================  

Configure your SIP phone / Soft phone  
Below are the default details to be used while configuring the phone  


| Key | Value |
| ------ | ------ |
| username, auth name, etc | `200` |
| password | `1234` |
| host / IP Address | This should be IP of the machine running the application.<br>It will vary on different machines and networks.<br>Run `ifconfig` or `ip a` in the ubuntu terminal to get the correct IP address.<br>For example it could be like `192.168.8.50`. |



Coding style
===========

We use the Python Enhancement Proposal (PEP) 8 style while coding.  
You can refer to this page [here](https://www.python.org/dev/peps/pep-0008/) for more info about the coding style.  


Before pushing code to the repository, please check for any coding style errors with the following command otherwise your pipelines will fail  
```bash
$ flake8 --max-line-length=120 --statistics ./run.py ./agi.py ./app
```

The output of this command with show you file names with errors or nothing if there ain't any.


To fix your coding style errors to match the coding style (PEP8) automatically, run the following command.
```bash
$ autopep8 --in-place --aggressive --aggressive <filename_with_errors or a directory>
```
Note. This tool may not fix some styling errors therefore there might be need for manual fixing.  


References
==========
Asterisk REST Interface (ARI) [Reference](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=29395573)  
This is the interface we use to get most of the asterisk details like sip peers, current channels etc.  

Asterisk Manager Interface (AMI) [Reference](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=4817239)  
This is the interface we use to initiate calls and get call responses from asterisk


Asterisk Gateway Interface (AGI) [Reference](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589)  
This is the interface we use to manipulate the asterisk language after parsing VXML


Beautiful Soup [Reference](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)  
This is the library we use to parse Voice XML (VXML) from external applications like MOTECH


Flask [Reference](https://flask.palletsprojects.com/en/1.1.x/)  
This is the library we use to develop the IVR API


Flake8 [Reference](http://flake8.pycqa.org/en/latest/user/configuration.html)  
Used for code style linting (checking).

Redis-Server [Reference](https://redis.io/documentation)    
The in-memory data structure store of preference used heavily in app.py

Autopep8 [Reference](https://pypi.org/project/autopep8/)  
Auto fixes code style errors
