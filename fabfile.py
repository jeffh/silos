import os

from fabric.api import task, env, roles, sudo, run, parallel, puts, reboot, cd, settings
from fabric.contrib.files import upload_template
from fabric.state import output
from cuisine import *

from crontab import Crontab
from hosts import *

output['everything'] = False
output['user'] = True

@task
def verbose():
    "Enables verbose output of everything."
    output['everything'] = True

###############################

@task
@parallel
def reboot_if_required():
    "Reboots the machine only if it's required"
    if file_exists('/var/run/reboot-required'):
        puts("Rebooting...")
        reboot()
        puts("Machine is back online.")
    else:
        puts("No reboot required.")

@task
def ssh_key(keypath=None, user=None):
    """Adds the local ssh key to the authorized_keys list for the given user.

    Defaults to ~/.ssh/id_rsa.pub and current user being ssh-ed in.
    """
    user = user or env.user
    keypath = keypath or '~/.ssh/id_rsa.pub'
    ssh_authorize(user, keypath)
    puts("Added ssh key %r for %r" % (keypath, user))

@task
@parallel
def add_cron_ping(url, freq='@hourly', template='curl -k %r'):
    """Adds a crontab entry to continously hit a url.

    Useful to quickly add a ping to afraid.org to update the ip address.
    Equal signs in the url must be escaped.
    """
    ct = Crontab().load()
    ct.add('%s %s' % (freq, template % url))
    ct.save()

@task
@parallel
def bootstrap(upgrade=0):
    """Basic set up of the system:
        - Adds default ssh-key
        - Upgrades packages
    """
    ssh_key()
    if int(upgrade):
        puts("Updating Sources...")
        package_update()
        puts("Upgrading Packages...")
        package_upgrade()
        reboot_if_required()

    ensure('unattended-upgrades')
    file_write('/etc/apt/apt.conf.d/20auto-upgrades', """APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";""", sudo=True)

    ensure('vim')

@task
def setup_python():
    ensure('python-pip')
    pip_ensure('virtualenv', use_sudo=True)

@task
@parallel
def setup_gitolite(pubkey='~/.ssh/id_rsa.pub', git_user='git'):
    """Installed a simple gitolite instance on the given machine with the provided
    public key as a the admin under a system user that all git users share.

    The public key defaults to your local ~/.ssh/id_rsa.pub.
    The default system user is 'git'.

    """
    puts("Ensure user %s..." % git_user)
    user_ensure(git_user, home='/home/%s' % git_user)
    ensure('gitolite')
    file_write('/tmp/pk.pub', file_local_read(pubkey))
    try:
        sudo('gl-setup -q /tmp/pk.pub', user=git_user)
        puts("You can now do 'git clone %s@%s:gitolite-admin.git'" % (git_user, env.host))
    finally:
        file_unlink('/tmp/pk.pub')

@task
@parallel
def setup_git_repo(remote_path, *hooks, **kwargs):
    """Initializes a bare git repo on the given remote path with optional git hooks.

    The hooks are a local files that gets uploaded as a git hooks. They should
    be named inline with their appropriate git/hooks. Any post-fixed dots are
    trimmed out before being uploaded. So, uploading 'post-receive.test' will
    upload as 'post-receive'.

    The scripts gets the follow variables interpolated into values as they are
    uploaded to the server:

        %(REPO)s refers to the path to the bare repository.

    With a custom post recieve script, various behaviors can be implemented,
    such as post-receive deploy scripts.

    Pass use_sudo=True to use sudo when creating repositories.
    """
    def full_path(p):
        if os.path.isabs(p):
            return p
        return os.path.join(run('pwd'), p)
    context = {
        'REPO': full_path(remote_path),
    }

    use_sudo = kwargs.pop('use_sudo', False)
    ensure('git-core')
    dir_ensure(remote_path, recursive=True)
    with cd(remote_path):
        puts("Init bare git repo %r..." % remote_path)
        (sudo if use_sudo else run)('git init --bare')

    dest = os.path.join(remote_path, 'hooks')
    dir_ensure(dest)

    puts("Paths: %r" % context)
    for hook in hooks:
        name = os.path.basename(hook).split('.')[0]
        fullpath = os.path.join(dest, name)
        puts("Hook %r -> %r..." % (name, fullpath))
        upload_template(hook, fullpath, context, use_sudo=use_sudo, backup=False)
        file_ensure(fullpath, mode='+x')

#######################################################

def ensure(package):
    puts("Ensuring system package %s..." % package)
    package_ensure(package)


def pip_ensure(package, env=None, upgrade=False, use_sudo=False):
    puts("Ensuring pip package %s..." % package)
    cmd = sudo if use_sudo else run
    cmd('PIP_NO_INPUT=1 pip install --use-mirrors %s %s %s' % (
        '--upgrade' if upgrade else '',
        '-E ' + env if env else '',
        package,
    ))
