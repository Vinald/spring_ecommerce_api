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
""")

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
os.system("cd ~/")
os.system("git clone https://github.com/zaf/asterisk-googletts.git")
os.system("cd asterisk-googletts*")
os.system("cp googletts.agi /var/lib/asterisk/agi-bin/")

print("""
Successfully installed Google TTS on your machine. You should be all good to go...
""")
