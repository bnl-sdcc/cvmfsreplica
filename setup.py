#!/usr/bin/env python
#

import commands
import os
import re
import sys

from distutils.core import setup
from distutils.command.install import install as install_org
from distutils.command.install_data import install_data as install_data_org


from cvmfsreplica import service
release_version = service.__version__ 

# ===========================================================
#                D A T A     F I L E S 
# ===========================================================


etc_files = ['etc/cvmfsreplica.conf',
             'etc/repositories.conf',
             ]

sysconfig_files = [ 'etc/sysconfig/cvmfsreplica', ]
logrotate_files = ['etc/logrotate/cvmfsreplica',]
initd_files = ['etc/cvmfsreplica',]


# -----------------------------------------------------------

rpm_data_files=[('/etc/cvmfsreplica', etc_files),
                ('/etc/sysconfig', sysconfig_files),
                ('/etc/logrotate.d', logrotate_files),                                        
                ('/etc/init.d', initd_files),
               ]

# -----------------------------------------------------------

def choose_data_files():
    rpminstall = True
    userinstall = False
     
    if 'bdist_rpm' in sys.argv:
        rpminstall = True

    elif 'install' in sys.argv:
        for a in sys.argv:
            if a.lower().startswith('--home'):
                rpminstall = False
                userinstall = True
                
    return rpm_data_files
       
# ===========================================================

# setup for distutils
setup(
    name="cvmfsreplica",
    version=release_version,
    description='cvmfsreplica package',
    long_description='''This package contains cvmfsreplica''',
    license='GPL',
    author='Jose Caballero',
    author_email='jcaballero@bnl.gov',
    maintainer='Jose Caballero',
    maintainer_email='jcaballero@bnl.gov',
    url='https://matrix.net',
    # we include the test/ subdirectory
    packages=['cvmfsreplica',
              'cvmfsreplica.pyconfidence',
              'cvmfsreplica.plugins',
              'cvmfsreplica.plugins.service',
              'cvmfsreplica.plugins.repository',
              'cvmfsreplica.plugins.repository.report',
              'cvmfsreplica.plugins.repository.acceptance',
              'cvmfsreplica.plugins.repository.post',
              'cvmfsreplica.test',
              'cvmfsreplica.test.unit',
              ],

    scripts = ['bin/cvmfsreplica', ],
    
    data_files = choose_data_files()
)
