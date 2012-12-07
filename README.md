Silos
=========

A collection of missiles to fire with a red button!
Err, I mean you can setup ubuntu-based servers easily with this.

Setup
----------

You'll need to install dependencies with [pip][1]. Run:

    pip install -r requirements.txt

This will install fabric, which is used to run the tasks
with the `fab` command.

[1]: http://www.pip-installer.org/en/latest/

Usage
----------

Use the `fab -l` to see all the lists commands:

    add_cron_ping
    bootstrap
    reboot_if_required
    setup_git_repo
    setup_gitolite
    setup_python
    add_key
    verbose

Use the `-H <server>` arg to run the commands on a server:

    fab -H root@ip-addr add_key bootstrap

This will add your own ssh key from ~/.ssh/id_rsa.pub to the authorized_keys,
then update your system, before finally installing `unattended-upgrades` and
`vim`.

### Store Hosts

Typing the host every time is annoying. Rename `hosts_sample.py` to `hosts.py`
and configure it to your needs.

Then you can prefix it with a nice name:

    fab pi add_key bootstrap

