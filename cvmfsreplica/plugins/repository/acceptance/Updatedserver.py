#!/usr/bin/env python

import logging
import os
import urllib

from cvmfsreplica.cvmfsreplicaex import PluginConfigurationFailure
from cvmfsreplica.interfaces import RepositoryPluginAcceptanceInterface
import cvmfsreplica.pluginsmanagement as pm


class Updatedserver(RepositoryPluginAcceptanceInterface):

    def __init__(self, repository, conf):
        self.log = logging.getLogger('cvmfsreplica.updatedserver')
        self.repository = repository
        self.conf = conf
        try:
            self.url = self.repository.cvmfsconf.get('CVMFS_STRATUM0')
            self.reportplugins = pm.readplugins(self.repository,
                                                'repository',
                                                'report',
                                                self.conf.namespace('acceptance.updatedserver.',
                                                                    exclude=True)
                                                )

        except:
            raise PluginConfigurationFailure('failed to initialize Updatedserver plugin')
        self.log.debug('plugin Updatedserver initialized properly')


    #def verify(self):
    #    '''
    #    checks if file .cvmfspublished
    #    was updated more recently than variable
    #    repository.last_published
    #    '''
    #    try:
    #        # FIXME
    #        # maybe we should try a couple of times in case of failures before failing definitely
    #        for line in urllib.urlopen('%s/.cvmfspublished' %self.url).readlines():
    #            if line.startswith('T'):
    #                time = int(line[1:-1])
    #                break
    #        out = time > self.repository.last_published
    #        if out == False:
    #            self._notify_failure('No new content at the server for repository %s' \
    #                                  %self.repository.repositoryname)
    #        return out
    #    except:
    #        self.log.warning('file %s/.cvmfspublished cannot be read. Returning False' %self.url)
    #        return False

    def verify(self):
        '''
        checks if the revision number in local copy of .cvmfspublished
        is different that the revision number of remote .cvmfspublished
        '''
        try:
            # FIXME
            # maybe we should try a couple of times in case of failures before failing definitely
            for line in urllib.urlopen('%s/.cvmfspublished' %self.url).readlines():
                if line.startswith('S'):
                    serverrevision = int(line[1:-1])
                    break

            # read the local revision number
            cvmfs_upstream_storage = self.repository._get_cvmfs_upstream_storage() # FIXME, this should not be here
            localfile = '%s/.cvmfspublished' %cvmfs_upstream_storage
            if not os.path.isfile(localfile):
                self.log.warning('local file %s does not exist. Returning True' %localfile)
                return True
            else:
                # FIXME: too much duplicated code
                for line in open(localfile):
                    if line.startswith('S'):
                        localrevision = int(line[1:-1])
                        break

            out = (serverrevision != localrevision)
            if out == False:
                self._notify_failure('No new content at the server for repository %s' \
                                      %self.repository.repositoryname)
            return out
        except:
            self.log.warning('file %s/.cvmfspublished cannot be read. Returning False' %self.url)
            return False



    def _notify_failure(self, msg):
        for report in self.reportplugins:
            report.notifyfailure(msg)

