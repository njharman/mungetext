import os
import re

from setuptools import find_packages, setup


def read_version():
    """Read __version__ from __init__.py."""
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    version = os.path.join(os.path.dirname(__file__), 'munge', 'version.py')
    with open(version) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        msg = 'Cannot find version in munge/__init__.py'
        raise RuntimeError(msg)


install_requires = []


setup(name='munge',
      version=read_version(),
      description='Parse and munge structured text',
      platforms=['POSIX'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=install_requires,
      zip_safe=False)
