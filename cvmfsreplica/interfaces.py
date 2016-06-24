class RepositoryPluginReportInterface(object):

    def notifyfailure(self, custommsg=None):
        '''
        notifies/reports when things go wrong.
        For example, when the "cvmfs_server snapshot"
        command fails.
        '''
        raise NotImplementedError

    def notifysuccess(self):
        '''
        notifies/reports when replication worked.
        '''
        raise NotImplementedError


class RepositoryPluginAcceptanceInterface(object):

    def verify(self):
        '''
        verifies some condition is True or False
        in order to accept replicating a repository
        '''
        raise NotImplementedError


    def _notify_failure(self, msg):
        '''
        call report plugins, if defined, to notify failure
        '''
        raise NotImplementedError


class RepositoryPluginPostInterface(object):

    def run(self):
        '''
        perform actions always after a replication
        was done, or attempted
        '''
        raise NotImplementedError

