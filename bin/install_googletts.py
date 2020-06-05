import os


print("""
Asterisk Google TTS Installer
============================================

This script shall install the needed dependencies for the Asterisk Google TTS Engine:

1. Perl
2. perl-libwww
3. perl-LWP-Protocol-https
4. Sox
5. MPG123

Reference guide available at: https://github.com/zaf/asterisk-googletts

NOTE:
--------
- If you have redis installed using Docker, you may see afew error messages during this installation.
  Most of the dependencies use redis and as such try to restart redis during the installation.
  Simply ignore the errors during the install process and restart your redis docker instance manually 
  after the installation.
  
- If redis is installed on the host itself, the installation should go smoothly.

- You may need to accept a prompt during the 'perl-LWP-Protocol-https' installation so look out for that.

Press 'return' or 'enter' if you wish to proceed with the installation or 'q' to cancel and exit.
""")


user_input = input(">> ")

if user_input == "":
    pass
elif user_input == "q" or "Q":
    print("Exiting Installation Script")
    exit(0)
else:
    print('Invalid Input. Exiting Script')
    exit(0)


os.system("apt update && apt upgrade -y")

print("""
Installing Perl
============================================
""")
os.system("curl -L http://xrl.us/installperlnix | bash")

print("""
Installing perl-libwww
============================================
""")
os.system("apt-get install -y libwww-perl")

print("""
Installing perl-LWP-Protocol-https
============================================
""")
os.system("cpan install LWP::Protocol::https")

print("""
Installing SOX
============================================
""")
os.system("apt install -y sox")
os.system("apt install libsox-fmt-mp3 -y")

print("""
Installing MPG123
============================================
""")
os.system("apt-get install -y mpg123")

print("""
Configure Google TTS
============================================
""")
os.system("cd /root")
os.system("git clone https://github.com/zaf/asterisk-googletts.git")
os.system("cd asterisk-googletts*")
os.system("cp googletts.agi /var/lib/asterisk/agi-bin/")
os.system("cd .. && rm -Rf asterisk-googletts*")

print("""
Successfully installed Google TTS on your machine. You should be all good to go...
""")
