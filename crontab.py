from fabric.api import run, sudo, settings, puts, env
import cuisine

class Crontab:
    def __init__(self, user=None):
        self.user = user
        self.lines = []

    def add(self, line):
        if line not in self:
            self.lines.append(line)

    def remove(self, line):
        self.lines.remove(line)

    def __contains__(self, line):
        return line in self.lines

    def __iter__(self):
        return iter(self.lines)

    def load(self):
        puts("Reading from %s's crontab..." % (self.user or env.user))
        cmd = sudo if self.user else run
        with settings(warn_only=True):
            output = cmd('crontab %s -l' % (
                ('-u ' + self.user) if self.user else ''
            ))
            if output.startswith('no crontab for '):
                self.lines = []
            else:
                self.lines = output.split('\n')
        return self

    def save(self):
        puts("Writing to %s's crontab..." % (self.user or env.user))
        cuisine.file_unlink('/tmp/new-crontab')
        cuisine.file_write('/tmp/new-crontab', '\n'.join(self.lines) + '\n')
        cmd = sudo if self.user else run
        try:
            cmd('crontab %s < /tmp/new-crontab' % (
                ('-u ' + self.user) if self.user else ''
            ))
        finally:
            cuisine.file_unlink('/tmp/new-crontab')
        return self


