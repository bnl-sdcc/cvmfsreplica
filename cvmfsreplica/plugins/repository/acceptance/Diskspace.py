#!/usr/bin/env python

import logging
import os

from cvmfsreplica.cvmfsreplicaex import PluginConfigurationFailure, AcceptancePluginFailed
from cvmfsreplica.interfaces import RepositoryPluginAcceptanceInterface
from cvmfsreplica.utils import check_disk_space
import cvmfsreplica.pluginsmanagement as pm


class Diskspace(RepositoryPluginAcceptanceInterface):

    def __init__(self, repository, conf):
        self.log = logging.getLogger('cvmfsreplica.diskspace')
        self.repository = repository
        self.conf = conf
        try:
           self.spool_size = self.conf.getint('diskspace.spool_size')
           self.storage_size = self.conf.getint('diskspace.storage_size')
           self.reportplugins = pm.readplugins(self.repository, 
                                               'repository', 
                                               'report', 
                                               self.conf.namespace('acceptance.diskspace.', 
                                                                   exclude=True)
                                               )
        except:
           raise PluginConfigurationFailure('failed to initialize Diskspace plugin')
        try:
            self.should_abort = self.conf.getboolean('diskspace.should_abort')
        except:
            self.should_abort = True #Default

        self.log.debug('plugin Diskspace initialized properly')


    def verify(self):
        '''
        checks if there is enough space in disk 
        '''

        try:
            return self._check_storage() & self._check_storage()
        except Exception, ex:
            raise ex


    def _check_spool(self):
        # FIXME: too much duplicated code

        SPOOL_DIR = self.repository.cvmfsconf.get('CVMFS_SPOOL_DIR')
        if check_disk_space(SPOOL_DIR, self.spool_size):
            self.log.trace('There is enough disk space for SPOOL directory')
            return True
        else:
            msg = 'There is not enough disk space for SPOOL. Requested=%s, available=%s' %(self.spool_size, current_free_size)
            self._notify_failure(msg)
            self.log.error(msg)
            if self.should_abort:
                self.log.error('Raising exception')
                raise AcceptancePluginFailed(msg)
            else:
                return False


    def _check_storage(self):
        # FIXME: too much duplicated code

        STORAGE_DIR = self.repository.cvmfsconf.get('CVMFS_UPSTREAM_STORAGE').split(',')[1]
        if check_disk_space(STORAGE_DIR, self.storage_size):
            self.log.trace('There is enough disk space for STORAGE directory')
            return True
        else:
            msg = 'There is not enough disk space for STORAGE. Requested=%s, available=%s' %(self.storage_size, current_free_size)
            self._notify_failure(msg)
            self.log.error(msg)
            if self.should_abort:
                self.log.error('Raising exception')
                raise AcceptancePluginFailed(msg)
            else:
                return False

    
    def _notify_failure(self, msg):
        for report in self.reportplugins:
            report.notifyfailure(msg)

        

