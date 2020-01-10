Getting Your IVR Setup
===================
This guide is essentially to help you get started with setting up MOTECH and Asterisk as well as setting up the python scripts 
as well as explain the use of some of the scripts included in this folder. 

Setting up your GitLab SSH
-----------------

This shall help with authentication with git. As opposed to authenticating with your username and password each time, you shall authenticate with SSH and wont need to use your credentials each time you wish to push or pull. On the Machine you wish to clone this repo too,

```
root@asterisk:~# ssh-keygen

Generating public/private rsa key pair.
Enter file in which to save the key (/root/.ssh/id_rsa):
Created directory '/root/.ssh'.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /root/.ssh/id_rsa.
Your public key has been saved in /root/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:4M1ANA+B06uFiP3BYKbTcdXNuCV3Cx+iBkK8svRBw3Q root@asterisk
The key's randomart image is:
+---[RSA 2048]----+
|   =o=Eo +       |
|  = Xoo++ B o    |
| B B *oo.* = o   |
|+ * *.o=+   o    |
| o = =..S        |
|  . +            |
|                 |
|                 |
|                 |
+----[SHA256]-----+

root@asterisk:~# cat ~/.ssh/id_rsa.pub

ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDK7ZdEc8u+nXd+w2WrFMMxQEnrRsU5cqANLocKIZYO8RZsbbqs2LdKpYQN4mT9mskLoZqhI1HANDnPfY2tJdcVAhLvJyR+qDkXjzrqe4oU1o3vDuRsasjE+rezt+M6X9+FGvOPGP3Byl6vyJd+qkV3cJcNspoW6ZWlXHXHp0UpF89TSxvHMUv5815pRuOYvVtOxYi12uS//Gds91aK7xMbT9MGVKlSSTqJ4oEm6MgZ4ueMC3OFIuwJdG+/d6Td7rQ+TIkyGe3IfiVzmBJ0w4iWASsPV9yYDs2X+ILIqBqK52BDhJQ/xSxGveXtYmZpkjjDaxoL5hGkUmXdQPsZBnlb root@asterisk

```

Copy the created key and in GitLab >> User Settings >> SSH Keys, copy and paste this key into the available space and save. This way you wont need to use your email and password each time you need to interact with the repo.

Once you are done with this, you need to delete the old repo and clone it again, this time round, clone it with **SSH** and not HTTP. That way, moving forward, you wont need to use your username and password to authenticate with interacting with Git.

Setting up Asterisk
=====

Prerequisites:
-----

* A VM with Ubuntu 18 LTS (The server version is most preferable for its speed). The VM should be updated and preferably have the following packages: vsftpd, openssh-server.

Follow the guide [here]("https://computingforgeeks.com/how-to-install-asterisk-16-lts-on-ubuntu-18-04-16-04-debian-9") to get Asterisk
set up on your local machine.

For the purposes of this setup, configure the following:

In the `/etc/asterisk/sip.conf` file, add the following lines, save and exit:

```
[256750046950]
        type=friend
        context=phones
        disallow=all
        allow=ulaw,alaw
        secret=12345678
        host=dynamic
        nat=yes

```
In this, your basically telling asterisk that it should recognise any 
peer that tries to authenticate with the user credentials:
- Username : 256750046950
- Password: 12345678

These are the credentials you would then configure on your SIP phone or 
soft phone. You are free to chage them though if you wish. Notice though that I used a **phone number** as the username. This is important as we shall later see that its this number captured as the **CallID** variable used in the AGI Script.

In the `/etc/asterisk/extensions.conf` file, add the following lines, save and exit:

```
[phones]
        exten => 0800113213,1,NoOp(This is a Test IVR)
        same => n,Answer
        same => n,AGI(agivxml.py)
        same => n,Hangup

```
This basically tells Asterisk that when  **0800113213** (The Current Toll Free number) is dialed, direct the call to the **agivxml.py** AGI file.

Once you are doe with that, refresh Asterisk so tht it can pick up the new configs 
by entering the commands:

```
asterisk -rvvv

Asterisk 16.6.2, Copyright (C) 1999 - 2018, Digium, Inc. and others.
Created by Mark Spencer <markster@digium.com>
Asterisk comes with ABSOLUTELY NO WARRANTY; type 'core show warranty' for details.
This is free software, with components licensed under the GNU General Public
License version 2 and other licenses; you are welcome to redistribute it under
certain conditions. Type 'core show license' for details.
Running as user 'asterisk'
Running under group 'asterisk'
Connected to Asterisk 16.6.2 currently running on asterisk (pid = 602)

asterisk*CLI>
asterisk*CLI> sip reload
 Reloading SIP
asterisk*CLI> dialplan reload
Dialplan reloaded.

```

You can check that your peers are registerd with Asterisk by running this commnd within the Asterisk CLI `sip show peers`

Your peers should be online if they have been successfully registered.

You shall need a soft phone on which you can test some of your calls. For my testing, I used jfPhone which is a Windows softphone
that can be found [here]("https://sourceforge.net/projects/jfphone/"). When you download, install this application and open it.

CFG (Its one of the Buttons) >> Accounts >> Line1 >>:

Display Name - Softphone

Username - 256750046950

Password - 12345678

Domain - 192.168.88.225 (Your Asterisk IP)

Remember, this are the configurations we made in the **sip.conf** file. Aftr this, it should successfully register and should be able and make calls.

For FTP, I use MobaXTerm that can be downloaded [here]("https://mobaxterm.mobatek.net/download.html"). In the Session tab, I use SFTP for my FTP. Make sure the credentials you 
use to login have the permission to read an write to the folder you want to write to. 
This shall come in handy for copying the audio files to the VM or copying the Motech Install Script. You must also have **vsftpd** installed on the linux machine you wish to FTP to.

Getting MOTECH Installed
===========

Prerequisites:
------

* A VM with Ubuntu 18 LTS (The server version is most preferable for its portability). The VM should be updated and preferably have the following packages: vsftpd, openssh-server.

* The VM should have atleast 15GB space.

Get access to the CFL install script and have it locally available on your new VM. The script can now be accessed [here]("http://gitlab.theacademy.co.ug/theacademy/scripts"). You can 
download or clone it from there.
Navigate to the directory and install the script:

```
cd cfl710/

./install-cfl710.sh

```
This may take up to 30 minutes. Once this is done. Run the command below to start the 
MOTECH containers:

```
docker ps
```

You shall have to wait for atleast 8 minutes from the moment you run this 
command for the MOTECH database to be ready for use. Take note of the IP of your local machine.
This is where the MOTECH database shall be accessed from.
You can then access the vxml callflow files. Am example is:

**"http://192.168.88.251/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?phone=256750046950"**

The **192.168.88.251** would represent the local IP for your VM.
To access the call flow for a particular number, add the **?phone=256750046950** infront of the **Mainflow.vxml**.
The phone number added must be in the MOTECH database for the correct call flow to be generated. Otherwise
the default call flow **"We_are_Sorry"** is what you shall be directed to. 

Please note that the phone numbr you select e.g. "256750046950" in our case must be in an "ACTIVATED" state in the database. You can check this
by logging into th database e.g 192.168.88.251:8080, using "root" for the username and password, then within motech_data_services, you access the "cfl_patients" table
and search for the number you wish to use for testing. Simply edit the state from "DEACTIVATED" to "ACTIVATED" and save the changes.

This nomenclature is what shall be used for options like **pin**, or **choice** when 
a user needs to choose an option in the IVR menu. For example, for pin, it would look like:

**"http://192.168.88.251/motech-platform-server/module/callflows/in/voxeo/flows/MainFlow.vxml?pin=1234"**
							
With this you should be able to interact with MOTECH successfully. Note that after the **Mainflow.vxml**,
the following links are autogenerated by MOTECH and are always different because for each link clicked or downloaded, a 
database entry is made/updated. The only link that is typically constant is the first **Mainflow.vxml** link.

## The AGI Python scripts

### agivxml.py
This is the main python file that shall be present in the Asterisk Dialplan. 
```
[phones]
        exten => 100,1,NoOp(This is a Test IVR)
        same => n,Answer
        same => n,AGI(agivxml.py)
        same => n,Hangup
```
**NOTE:** This AGI script should be stored in the directory **/var/lib/asterisk/agi-bin/**, which is Asterisk's default directory for AGI files.

