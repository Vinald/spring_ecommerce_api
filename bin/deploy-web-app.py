import os
import pathlib
import subprocess
import sys

working_dir = os.path.dirname(os.path.realpath(__file__))
project_dir = pathlib.Path(working_dir).parent

web_dir = os.path.join(project_dir, 'web')
env_file = os.path.join(web_dir, '.env')

env_local_file = os.path.join(web_dir, '.env.development')

apache_dir = '/etc/apache2'

if not os.path.exists(apache_dir):
    os.system("mkdir -p {}".format(apache_dir))

htpasswd_file = os.path.join(apache_dir, '.htpasswd')

# nginx web root directory for the web app
web_build_dir = os.path.join(web_dir, 'dist')

if not os.path.exists(env_file):
    os.system("cp {} {}".format(env_local_file, env_file))

os.system("apt-get update && apt install nginx apache2-utils curl -y")

# Check if npm exists on system
output = subprocess.getoutput('which npm')

if len(output) <= 0:
    os.system("curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash - && sudo apt-get install -y nodejs")

os.chdir(web_dir)
print("Current working dir: {}".format(os.getcwd()))

old_api_route = 'http://172.18.0.1:5000/api'
new_api_route = 'http://$(curl http://icanhazip.com):5000/api'

cmd = 'sed -i "s+VUE_APP_ROOT_API={}+VUE_APP_ROOT_API={}+g" .env'
os.system(cmd.format(old_api_route, new_api_route))

os.system("npm config set unsafe-perm true")
os.system("npm install")
os.system("npm run build")

config = """server {{
    listen 8000;

    root {};
    index index.html;
    server_name _;

    auth_basic "Administrator's Area";
    auth_basic_user_file {};

    location / {{
        # First attempt to serve request as file, then
        # as directory, then fall back to displaying a 404.
        try_files $uri $uri/ /index.html;
    }}

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {{
        root /usr/share/nginx/html;
    }}
}}"""

web_root_dir = "/var/www/html/ivr-web-app"

os.system("rm -rf {}".format(web_root_dir))
os.system("mv {} {}".format(web_build_dir, web_root_dir))
os.system("htpasswd -b -c {} ivr_admin 12345Uganda**".format(htpasswd_file))

file = open('/etc/nginx/sites-available/ivr-web-app', 'w')
file.write(config.format(web_root_dir, htpasswd_file))
file.close()

os.system("chown -R www-data:www-data {} {}".format(web_root_dir, htpasswd_file))
os.system("chmod -R 775 {} {}".format(web_root_dir, htpasswd_file))

os.system("ln -s /etc/nginx/sites-available/ivr-web-app /etc/nginx/sites-enabled/")
os.system("nginx -t")
os.system("systemctl reload nginx")

sys.exit()
