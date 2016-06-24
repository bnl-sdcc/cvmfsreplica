#!/usr/bin/env python

import logging
import os
import subprocess 

from cvmfsreplica.cvmfsreplicaex import PluginConfigurationFailure
from cvmfsreplica.interfaces import RepositoryPluginPostInterface



class Cleanup(RepositoryPluginPostInterface):

    def __init__(self, repository, conf):
        self.log = logging.getLogger('cvmfsreplica.cleanup')
        self.repository = repository
        self.conf = conf
        try:
            self.CVMFS_SRV_DIRECTORY = \
                 self.repository.cvmfsconf.get('CVMFS_UPSTREAM_STORAGE')\
                 .split(',')[1]
        except:
            raise PluginConfigurationFailure(
                   'failed to initialize Cleanup plugin'
                  )
        self.log.debug('plugin Cleanup initialized properly')

    def run(self):
        dir_exists = os.path.isdir(self.CVMFS_SRV_DIRECTORY)
        if not dir_exists:
            self.log.warning('directory %s does not exist. Nothing to do.' %self.CVMFS_SRV_DIRECTORY)
        else:
            files = os.listdir(self.CVMFS_SRV_DIRECTORY) 
            for file in files:
                os.remove('%s/%s' %(self.CVMFS_SRV_DIRECTORY, file))
      

