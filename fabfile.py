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
REPO = "https://github.com/dylanjbarth/django-wedding-website"

@task
def systemctl(c, command):
    c.run(f"sudo systemctl {command}")

@task
def update_packages(c):
    c.run(f"sudo apt-get update && sudo apt-get -y upgrade")
    c.run(f"sudo apt-get install -y python3-pip python3-venv build-essential libssl-dev libffi-dev python-dev nginx")

@task
def update_code(c):
    if not c.run(f"sudo test -d {CODE_DIR}", warn=True):
        c.run(f"sudo git clone {REPO} {CODE_DIR}")
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
    c.run(f"cd {CODE_DIR} && sudo {VENV_PYTHON} manage.py collectstatic")

@task
def configure_gunicorn(c):
    with open('./deploy/gunicorn.service', 'r') as rf:
        data = rf.read()
    c.sudo(f"echo '{data}' | sudo tee -a /etc/systemd/system/gunicorn.service")
    systemctl(c, 'daemon-reload')
    systemctl(c, 'start gunicorn')
    systemctl(c, 'enable gunicorn')
    systemctl(c, 'restart gunicorn')

@task
def configure_nginx(c):
    with open('./deploy/nginx.gunicorn.conf', 'r') as rf:
        data = rf.read()
    c.run(f"sudo echo '{data}' | sudo tee -a /etc/nginx/sites-available/gunicorn")
    if not c.run(f"sudo test /etc/nginx/sites-enabled/gunicorn", warn=True):
        c.run(f"sudo ln -s /etc/nginx/sites-available/gunicorn /etc/nginx/sites-enabled/")
    systemctl(c, 'restart nginx')


@task
def deploy_full(c):
    update_packages(c)
    update_code(c)
    update_venv(c)
    migrate(c)
    configure_gunicorn(c)
    configure_nginx(c)

@task
def deploy(c):
    update_code(c)
    update_venv(c)
    migrate(c)
    configure_gunicorn(c)
    configure_nginx(c)

# if env.ssh_config_path and os.path.isfile(os.path.expanduser(env.ssh_config_path)):
#     env.use_ssh_config = True


# env.project = 'bigday'
# env.code_branch = 'master'
# env.sudo_user = 'czue'

# ENVIRONMENTS = ('production',)

# @task
# def _setup_path():
#     env.root = posixpath.join(env.home, 'www', env.environment)
#     env.hosts = ['czue.org']
#     env.log_dir = posixpath.join(env.home, 'www', env.environment, 'log')
#     env.code_root = posixpath.join(env.root, 'code_root')
#     env.project_media = posixpath.join(env.code_root, 'media')
#     env.virtualenv_root = posixpath.join(env.root, 'python_env')
#     env.services = posixpath.join(env.home, 'services')
#     env.db = '%s_%s' % (env.project, env.environment)

# @task
# def production():
#     env.home = "/home/czue"
#     env.environment = 'bigday'
#     env.django_port = '9091'
#     _setup_path()


# def update_code():
#     with cd(env.code_root):
#         sudo('git fetch', user=env.sudo_user)
#         sudo('git checkout %(code_branch)s' % env, user=env.sudo_user)
#         sudo('git reset --hard origin/%(code_branch)s' % env, user=env.sudo_user)
#         # remove all .pyc files in the project
#         sudo("find . -name '*.pyc' -delete", user=env.sudo_user)

# @task
# def deploy():
#     """
#     Deploy code to remote host by checking out the latest via git.
#     """

#     require('root', provided_by=ENVIRONMENTS)
#     try:
#         execute(update_code)
#         execute(update_virtualenv)
#         execute(migrate)
#         execute(_do_collectstatic)
#     finally:
#         # hopefully bring the server back to life if anything goes wrong
#         execute(services_restart)
#         pass


# @task
# def update_virtualenv():
#     """
#     Update external dependencies on remote host assumes you've done a code update.
#     """
#     require('code_root', provided_by=ENVIRONMENTS)
#     files = (
#         posixpath.join(env.code_root, 'requirements.txt'),
#         posixpath.join(env.code_root, 'deploy', 'prod-requirements.txt'),
#     )
#     for req_file in files:
#         cmd = 'source %s/bin/activate && pip install -r %s' % (
#             env.virtualenv_root,
#             req_file
#         )
#         sudo(cmd, user=env.sudo_user)


# def touch_supervisor():

#     touch supervisor conf files to trigger reload. Also calls supervisorctl
#     update to load latest supervisor.conf

#     require('code_root', provided_by=ENVIRONMENTS)
#     supervisor_path = posixpath.join(posixpath.join(env.services, 'supervisor'), 'supervisor.conf')
#     sudo('touch %s' % supervisor_path, user=env.sudo_user)
#     _supervisor_command('update')


# def services_start():
#     ''' Start the gunicorn servers '''
#     require('environment', provided_by=ENVIRONMENTS)
#     _supervisor_command('update')
#     _supervisor_command('reload')
#     _supervisor_command('start  all')

# def services_stop():
#     ''' Stop the gunicorn servers '''
#     require('environment', provided_by=ENVIRONMENTS)
#     _supervisor_command('stop all')


# def services_restart():
#     ''' Stop and restart all supervisord services'''
#     require('environment', provided_by=ENVIRONMENTS)
#     _supervisor_command('stop all')
#     _supervisor_command('start  all')


# def migrate():
#     """ run south migration on remote environment """
#     require('code_root', provided_by=ENVIRONMENTS)
#     with cd(env.code_root):
#         sudo('%(virtualenv_root)s/bin/python manage.py migrate --noinput' % env, user=env.sudo_user)

# def _do_collectstatic():
#     """
#     Collect static after a code update
#     """
#     with cd(env.code_root):
#         sudo('%(virtualenv_root)s/bin/python manage.py collectstatic --noinput' % env, user=env.sudo_user)

# @task
# def collectstatic():
#     """ run collectstatic on remote environment """
#     require('code_root', provided_by=ENVIRONMENTS)
#     update_code()
#     _do_collectstatic()


# def _supervisor_command(command):
#     require('hosts', provided_by=ENVIRONMENTS)
#     sudo('supervisorctl %s' % (command), shell=False, user='root')

# @task
# def print_supervisor_files():
#     for fname in os.listdir('deploy/supervisor'):
#         with open(os.path.join('deploy', 'supervisor', fname)) as f:
#             print('%s:\n\n' % fname)
#             print(f.read() % env)
