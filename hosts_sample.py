from fabric.api import env task

@task
def pi(): env.hosts += ['pi@pi']

@task
def virtualbox():
    env.hosts += ['jeff@192.168.1.2']
    env.passwords[env.hosts[-1]] = 'p'
