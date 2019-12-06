The agi-test.agi script is essential for having communication to asterisk through Python. For the purpose of this project,
I have added some DEMO functions to assist with the basic functions that I think shall be needed for this IVR Implementation.

Attached as well are files showing my test configurations in asterisk that I used whilst testing this deployment.

Afew points to note to get yourself setup:

In the /etc/asterisk/sip.conf file, add the following lines, save and exit:
""""
[ivrtest]
        type=friend
        context=phones
        allow=ulaw,alaw
        secret=12345678
        host=dynamic

""""
In this, your basically telling asterisk that i should recognise any peer that tries to authenticate with the user credentials:
Username : ivrtest
Password: 12345678

These are the credentials you would then configure on your SIP phone or soft phone. You are free to chage them though if you wish.

In the /etc/asterisk/extensions.conf file, add the following lines, save and exit:

""""
[phones]
        exten => 100,1,NoOp(This is a Test IVR)
        same => n,Answer
;       same => n,Saynumber(1)
;       same => n,Playback(/home/asteriskuser/en/001_02_01_TAMAGreeting1Generic)
;       same => n,MP3Player(/home/asteriskuser/en/001_02_01_TAMAGreeting1Generic.mp3)
        same => n,AGI(/home/asteriskuser/pyfiles/agi-test.agi)
        same => n,Hangup

""""

This basically tells Asterisk that when any phone/peer that is connected to it Dials 100, then that Dialplan should be followed.
Lines starting with ";" are commented out lines showing some basic Dialplan applications. Our focus shall be on the AGI and that is how
it is referenced in Asterisk.



Once you are doe with that, refresh Asterisk so tht it can pick up the new cofigs by entering the commands:
""""
:# asterisk -rvvv

Asterisk 16.6.2, Copyright (C) 1999 - 2018, Digium, Inc. and others.
Created by Mark Spencer <markster@digium.com>
Asterisk comes with ABSOLUTELY NO WARRANTY; type 'core show warranty' for details.
This is free software, with components licensed under the GNU General Public
License version 2 and other licenses; you are welcome to redistribute it under
certain conditions. Type 'core show license' for details.
=========================================================================
Running as user 'asterisk'
Running under group 'asterisk'
Connected to Asterisk 16.6.2 currently running on asterisk (pid = 602)
asterisk*CLI>
asterisk*CLI> sip reload
 Reloading SIP
asterisk*CLI> dialplan reload
Dialplan reloaded.

""""

You can check that your peers are registerd with Asterisk by running this commnd within the Asterisk CLI:
""""
sip show peers
""""

Your peers should be online if they have been successfully registered.







