import os
import pathlib

working_dir = os.path.dirname(os.path.realpath(__file__))
project_dir = pathlib.Path(working_dir).parent

web_dir = os.path.join(project_dir, 'web')
env_file = os.path.join(web_dir, '.env')
env_local_file = os.path.join(web_dir, '.env.development')

# nginx web root directory for the web app
web_root_dir = os.path.join(web_dir, 'dist')

if not os.path.exists(env_file):
    os.system("cp {} {}".format(env_local_file, env_file))

os.system("apt-get update && apt install nginx curl -y")
os.system("curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash - && sudo apt-get install -y nodejs")

os.chdir(web_dir)
print("Current working dir: {}".format(os.getcwd()))

old_api_route = 'http://127.0.0.1:5000/api'
new_api_route = 'http://$(curl http://icanhazip.com):5000/api'
cmd = 'sed -i "s+VUE_APP_ROOT_API={}+VUE_APP_ROOT_API={}+g" .env'
os.system(cmd.format(old_api_route, new_api_route))

os.system("npm config set unsafe-perm true")
os.system("npm install")
os.system("npm run build")

config = """server {{
        listen 8000 default_server;
        listen [::]:8000 default_server;

        root {};

        # Add index.php to the list if you are using PHP
        index.html;

        server_name _;

        location / {{
                # First attempt to serve request as file, then
                # as directory, then fall back to displaying a 404.
                try_files $uri $uri/ =404;
        }}
}}"""

file = open('/etc/nginx/sites-available/webapp', 'w')
file.write(config.format(web_root_dir))
file.close()

os.system("chown -R asterisk:www-data /root")
os.system("chmod -R 775 {}".format(web_root_dir))

os.system("ln -s /etc/nginx/sites-available/ivr-web-app /etc/nginx/sites-enabled/")
os.system("nginx -t")
os.system("systemctl reload nginx")
