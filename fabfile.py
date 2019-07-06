"""
Server layout:
    ~/services/supervisor/
        holds the configurations for these applications
        for each environment (staging, demo, etc) running on the server.
        Theses folders are included in the /etc/supervisor configuration.
    ~/www/
        This folder contains the code, python environment, and logs
        for each environment (staging, demo, etc) running on the server.
        Each environment has its own subfolder named for its evironment
        (i.e. ~/www/staging/logs and ~/www/demo/logs).
"""
# from invoke import Exit
# from invocations.console import confirm
import os
from fabric import task

CODE_DIR = "/opt/django-wedding-website"
VENV_PATH = os.path.join(CODE_DIR, '.env')
VENV_PYTHON = os.path.join(CODE_DIR, '.env/bin/python')
VENV_PIP = os.path.join(CODE_DIR, '.env/bin/pip3')
ACTIVATE_PATH = os.path.join(VENV_PATH, 'bin/activate')
REQUIREMENTS = os.path.join(CODE_DIR, "requirements.txt")
STATIC_ROOT = "/var/www/dylanandalex.love/"
REPO = "https://github.com/dylanjbarth/django-wedding-website"

@task
def systemctl(c, command):
    c.run(f"sudo systemctl {command}")

@task
def update_packages(c):
    c.sudo("apt-get update")
    c.sudo("apt-get -y upgrade")
    c.sudo("apt-get install -y python3-pip python3-venv build-essential libssl-dev libffi-dev python-dev nginx software-properties-common")
    c.sudo("add-apt-repository universe")
    c.sudo("add-apt-repository ppa:certbot/certbot")
    c.sudo("apt-get update")
    c.sudo("apt-get install -y certbot python-certbot-nginx")

@task
def update_code(c):
    if not c.run(f"sudo test -d {CODE_DIR}", warn=True):
        c.run(f"sudo git clone {REPO} {CODE_DIR}")
    c.run(f"cd {CODE_DIR} && sudo git fetch origin")
    c.run(f"cd {CODE_DIR} && sudo git reset --hard origin/master")
    c.run(f"cd {CODE_DIR} && sudo git pull")
    with open('./bigday/localsettings.py.prod', 'r') as rf:
        data = rf.read()
    # c.sudo(f"echo '{data}' | sudo tee -a {CODE_DIR}/bigday/localsettings.py")
    c.put('./bigday/localsettings.py.prod')
    c.sudo(f"mv localsettings.py.prod {CODE_DIR}/bigday/localsettings.py")
    c.run(f"cd {CODE_DIR} && sudo touch app.wsgi")

@task
def update_venv(c):
    if not c.run(f"sudo test -d {VENV_PATH}", warn=True):
        c.run(f"sudo python3 -m venv {VENV_PATH}")
    c.run(f"source {ACTIVATE_PATH} && sudo {VENV_PIP} install -r {REQUIREMENTS}")
    c.run(f"source {ACTIVATE_PATH} && sudo {VENV_PIP} install gunicorn")

@task
def migrate(c):
    c.run(f"cd {CODE_DIR} && sudo {VENV_PYTHON} manage.py migrate")

@task
def collect_static(c):
    if not c.run(f"sudo test -d {STATIC_ROOT}", warn=True):
        c.run(f"sudo mkdir -p {STATIC_ROOT}")
    c.run(f"cd {CODE_DIR} && sudo {VENV_PYTHON} manage.py collectstatic --noinput --clear")

@task
def configure_gunicorn(c):
    c.put('./deploy/gunicorn.service')
    c.sudo(f"mv gunicorn.service /etc/systemd/system/gunicorn.service")
    systemctl(c, 'daemon-reload')
    systemctl(c, 'start gunicorn')
    systemctl(c, 'enable gunicorn')
    systemctl(c, 'restart gunicorn')

@task
def configure_nginx(c):
    c.put('./deploy/nginx.gunicorn.conf')
    c.sudo(f"mv nginx.gunicorn.conf /etc/nginx/sites-available/gunicorn")
    if not c.run(f"sudo test /etc/nginx/sites-enabled/gunicorn", warn=True):
        c.run(f"sudo ln -s /etc/nginx/sites-available/gunicorn /etc/nginx/sites-enabled/")
    systemctl(c, 'restart nginx')

# @task
# def configure_certbot(c):
# https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx
# sudo certbot --nginx
# One time setup

@task
def set_dev_mode(c):
    c.put('./deploy/under_construction.html')
    c.sudo(f"mv under_construction.html /var/www/dylanandalex.love/under_construction.html")

@task
def unset_dev_mode(c):
    c.run(f"sudo rm /var/www/dylanandalex.love/under_construction.html")

@task
def deploy(c):
    update_packages(c)
    update_code(c)
    update_venv(c)
    collect_static(c)
    migrate(c)
    configure_gunicorn(c)
    configure_nginx(c)
    # configure_certbot(c)
