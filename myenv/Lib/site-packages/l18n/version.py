import subprocess
from datetime import datetime

__version_info__ = (2021, 3, 0, 'final', 0)


def get_version(version=__version_info__):

    dev_st = {'alpha': 'a', 'beta': 'b', 'rc': 'c', 'final': ''}

    assert len(version) == 5
    assert version[3] in dev_st.keys()

    n = 2 + (version[2] != 0)
    version_str = '.'.join([str(v) for v in version[:n]])

    if version[3] == 'final':
        return version_str

    if version[3:] == ('alpha', 0):
        return '%s.dev0+%s' % (datetime.utcnow().strftime("%Y.%m.%d"), get_git_chgset())
    else:
        return ''.join((version_str, dev_st[version[3]], str(version[4])))


def get_git_chgset():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                       universal_newlines=True).strip()[:-1]
    except:
        return '?'


__version__ = get_version()
