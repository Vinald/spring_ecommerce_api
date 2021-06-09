import os
import pathlib
import subprocess
import sys

working_dir = os.path.dirname(os.path.realpath(__file__))
project_dir = pathlib.Path(working_dir).parent

web_dir = os.path.join(project_dir, 'web')
env_file = os.path.join(web_dir, '.env')

env_local_file = os.path.join(web_dir, '.env.development')

# nginx web root directory for the web app
web_build_dir = os.path.join(web_dir, 'dist')

if not os.path.exists(env_file):
    os.system(f"cp {env_local_file} {env_file}")

os.system("apt-get update && apt install nginx curl -y")

# Check if npm exists on system
output = subprocess.getoutput('which npm')

if len(output) <= 0:
    os.system("curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash - && sudo apt-get install -y nodejs")

os.chdir(web_dir)
print(f"Current working dir: {os.getcwd()}")

old_api_route = 'http://172.18.0.1:5000/api'
new_api_route = 'http://$(curl http://icanhazip.com):5000/api'

cmd = f'sed -i "s+VUE_APP_ROOT_API={old_api_route}+VUE_APP_ROOT_API={new_api_route}+g" .env'
os.system(cmd)

os.system("npm config set unsafe-perm true")
os.system("npm install")
os.system("npm run build")

web_root_dir = "/var/www/html/ivr-web-app"

config = f"""server {{
    listen 8000;

    root {web_root_dir};
    index index.html;
    server_name _;

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


os.system(f"rm -rf {web_root_dir}")
os.system(f"mv {web_build_dir} {web_root_dir}")

file = open('/etc/nginx/sites-available/ivr-web-app', 'w')
file.write(config)
file.close()

os.system(f"chown -R www-data:www-data {web_root_dir}")
os.system(f"chmod -R 775 {web_root_dir}")

os.system("ln -s /etc/nginx/sites-available/ivr-web-app /etc/nginx/sites-enabled/")
os.system("nginx -t")
os.system("systemctl reload nginx")

sys.exit()
