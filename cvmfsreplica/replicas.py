#!/usr/bin/env python 

"""
module with all code to manage the replica threads
"""

import logging
import Queue
import subprocess
import threading
import time

import cvmfsreplica.pluginsmanagement as pm
import cvmfsreplica.utils as utils
from cvmfsreplica.cvmfsreplicaex import PluginConfigurationFailure, AcceptancePluginFailed

#from pyconfidence import SingleSectionConfig
from cvmfsreplica.pyconfidence import SingleSectionConfig
from cvmfsreplica.cvmfsreplicaex import RepositoriesConfigurationFailure


# =============================================================================
#       CLASS REPLICA MANAGER
# =============================================================================

class ReplicaManager:
    """
    class to handle all the components 
    involved in the process to request and
    run repositories snapshots.

    This class includes:

        -- a series of instances of a class 
           that represents each repository
           and time to time requests a snapshot.
           There is one instance per section in 
           the repositories configuration file
           (that is not disabled). 
           Each one of these objects is a thread.
        
        -- the [only] one instance of the 
           class that acts as a pipe to serialize
           the snapshot requests.
           
        -- N instances of a customer class
           that gets the Requests from the pipe
           and actually performs the snapshots.
           N is the maximum number of concurrent 
           snapshots we allow to happens simultaneously.
           Each one of these objects is a thread.
    """

    def __init__(self, service):
        """
        service is a reference to the class that creates 
        an object ReplicaManager. It contains, for example, 
        the configuration.
        """

        self.log = logging.getLogger('cvmfsreplica.replicamanager')

        self.service = service
        self.conf = service.conf
        self.repositoriesconf = service.repositoriesconf

        # list with all Repository( ) objects
        self.repositories = []

        # list with all ReplicaAgent( ) objects
        self.replicaagents = []

        self.replicarequestqueue = ReplicaRequestQueue()

        self._create_repositories()
        self._create_replica_agents()


    def _create_repositories(self):
        """
        creates, but does not start, 
        all Repository() thread objects
        """

        for section in self.repositoriesconf.sections():
            if self.repositoriesconf.getboolean(section, 'enabled'):
                repositoryname = self.repositoriesconf.get(section, 'repositoryname')
                self.log.debug('creating Repository() thread for %s' %repositoryname)
                singlerepositoryconf = self.repositoriesconf.getSection(section)
                try:
                    repository = Repository(self, repositoryname, singlerepositoryconf)
                except RepositoriesConfigurationFailure, ex:
                    self.log.critical(ex)
                self.repositories.append(repository)
            

    def _create_replica_agents(self):
        """
        creates, but does not start, 
        all ReplicaAgent() thread objects
        """
        
        for i in range(self.service.maxthreads):
            self.log.debug('creating ReplicaAgent() thread')
            self.replicaagents.append(ReplicaAgent(self, i))


    def run(self):
        """
        starts all threads:
            -- Repository object threads
            -- ReplicaAgent object threads

        and then wait, for ever, unless the daemon is stop
        """
        self._start_threads()
        self._wait()       


    def _start_threads(self):

        self.log.debug('starting all Repository() threads') 
        for repository in self.repositories:
            repository.start()

        self.log.debug('starting all ReplicaAgent() threads') 
        for replicaagent in self.replicaagents:
            replicaagent.start()


    def _wait(self):     

        try:
            while True:
                time.sleep(10)
                self.log.trace('Checking for interrupt.')

        except (KeyboardInterrupt):
            self.log.info("Shutdown via Ctrl-C or -INT signal.")
            self.shutdown()
            raise

        self.log.info("Leaving.")
       


    def shutdown(self):
        """
        stopts all threads:
            -- Repository object threads
            -- ReplicaAgent object threads
        """
        
        self.log.debug('stoping all Repository() threads') 
        for repository in self.repositories:
            repository.join()

        self.log.debug('stoping all ReplicaAgent() threads') 
        for replicaagent in self.replicaagents:
            replicaagent.join()



# =============================================================================
#       CLASS REPOSITORY
# =============================================================================


class Repository(threading.Thread):
    """
    class to represents each repository.

    There is one instance of this class per section
    in the repositories configuration file.

    This class, time to time, puts a ReplicaRequest object
    into a pipe, and wait for the Request to be done.
    """

    def __init__(self, manager, repositoryname, conf):
        """
        manager is a reference to the ReplicaManager class
        that created object Repository
        It includes needed things like object self.replicarequestqueue
        
        repositoryname is the name of the repository
        this class is handling.
        It comes from the configuration key "repository"
    
        conf is Config object, with cotent only for this repository
        """
        # NOTE: we pass repositoryname as input value
        #       so it can be used in the logger name
        #       before conf is even read

        threading.Thread.__init__(self) # init the thread
        self.log = logging.getLogger('cvmfsreplica.repository[%s]' %repositoryname)
        self.stopevent = threading.Event()

        self.manager = manager
        self.repositoryname = repositoryname
        self.conf = conf
        #self.repositoryname = self.conf.get("repositoryname") 
        self.interval = self.conf.getint("interval")
        self.ntrials = self.conf.getint("ntrials")
        if self.conf.has_option("priority"):
            self.priority = self.conf.getint("priority")
        else:
            self.priority = 0
        try:
            self._get_cvmfs_config()
            self.reportplugins = pm.readplugins(self, 'repository', 'report', self.conf)
            self.acceptanceplugins = pm.readplugins(self, 'repository', 'acceptance', self.conf)
            self.postplugins = pm.readplugins(self, 'repository', 'post', self.conf)
            self._readtimeout()
        except:
            raise RepositoriesConfigurationFailure(
                  'configuration for repository %s cannot be read' %self.repositoryname)

        # CMFS configuration:
        # getting the file with the time stampt for the last snapshot
        cvmfs_upstream_storage = self._get_cvmfs_upstream_storage()
        self.timestampfilename = '%s/.cvmfs_last_snapshot' %cvmfs_upstream_storage
        self.last_attempt = self.last_published = self._snapshotdate()


    def _readtimeout(self):
        # FIXME too much duplicated code
        """
        gets the timeout, when specified
        """
        self.timeout = None
        if self.conf.has_option('timeout'):
            self.timeout = self.conf.getint('timeout')


    def _get_cvmfs_config(self):

        self.cvmfsconf = SingleSectionConfig()
        self.cvmfsconf.ascii(
            open('/etc/cvmfs/repositories.d/%s/server.conf' %self.repositoryname)
        )


    def _get_cvmfs_upstream_storage(self):

        ###conf = SingleSectionConfig()
        ###conf.ascii('/etc/cvmfs/repositories.d/%s/server.conf' %self.repositoryname)
        CVMFS_UPSTREAM_STORAGE = self.cvmfsconf.get('CVMFS_UPSTREAM_STORAGE')
        CVMFS_UPSTREAM_STORAGE = CVMFS_UPSTREAM_STORAGE.split(',')[-1]
        return CVMFS_UPSTREAM_STORAGE


    def _snapshotdate(self):
        '''
        returns, in seconds since EPOCH, last time a repository was updated
        '''
        try:
            timestamp = open(self.timestampfilename)\
                        .readlines()\
                        [0]\
                        [:-1]
            secs = utils.date2seconds(timestamp)
            return secs
        except:
            self.log.warning('failed to open file %s. Returning 0' %self.timestampfilename)
            return 0


    def run(self):
        '''
        Method called by thread.start()
        Main functional loop.
        '''

        self.log.debug('starting Repository thread main loop...')
        while not self.stopevent.isSet():
            self.log.trace('Repository loop')
            age = int(time.time()) - self.last_attempt

            if self.last_attempt == 0:
                self.log.info('Repository %s never been replicated yet' %self.repositoryname)
            else:
                self.log.info('Last time repository %s was updated (or tried) was %s seconds ago' %(self.repositoryname, age))

            if self.interval > age:
                t_wait = self.interval - age
                self.log.info('waiting %s seconds for repository %s' %(t_wait, self.repositoryname))
                time.sleep(t_wait)

            try:
                if self._verify_acceptance():
                    self._request()
                    self._runpost()
                self.last_attempt = int(time.time())
            except AcceptancePluginFailed, ex:
                msg = 'An AcceptancePluginFailed exception was raised with message '
                msg += '"%s".' %ex
                msg += ' Stopping thread for repository %s' %self.repositoryname
                self.log.critical(msg)
                self.stopevent.set()


    def _verify_acceptance(self):
        '''
        checks all acceptance plugins say OK
        '''
        for acceptance in self.acceptanceplugins:
            if not acceptance.verify():
                self.log.info('acceptance plugin %s returned False' %acceptance)
                return False
        self.log.info('all acceptance plugins returned True. Ready to try snapshot')
        return True


    def _request(self):
        '''
        proceed with the request, 
        and post-request steps
        '''
        rc = self._put_request()
        if rc == 0:
            self._notify_success()
        else:
            self._notify_failure()
        self.last_published = int(time.time())


    def _put_request(self):
        '''
        puts a request object in the queue, 
        and waits for it to be done
        '''

        req = ReplicaRequest(self)
        self.manager.replicarequestqueue.put(req)
        while not req.done:
            time.sleep(1)
        rc = req.status
        self.log.info('Request for repository %s processed with final status %s' %(self.repositoryname, rc)) 
        return rc


    def _notify_success(self):
         for report in self.reportplugins:
             report.notifysuccess() 

    def _notify_failure(self):
         for report in self.reportplugins:
             report.notifyfailure() 

    def _runpost(self):
         for post in self.postplugins:
             post.run() 


    def join(self,timeout=None):
        '''
        Stop the thread. Overriding this method required to handle Ctrl-C from console.
        '''
        self.stopevent.set()
        self.log.debug('Stopping thread...')
        threading.Thread.join(self, timeout)


# =============================================================================
#       CLASS REPLICA REQUEST 
# =============================================================================


class ReplicaRequest(object):
    """
    This class represents a request to perform a snapshot
    for a given repository.

    Objects of this class are created by Repository( ) threads,
    piped into ReplicaRequestQueue( ) queue, 
    and grabbed by ReplicaThreadAgent( ) threads. 
    """

    def __init__(self, repository):

        self.log = logging.getLogger('cvmfsreplica.replicarequest')
        self.repository = repository
        self.repositoryname = self.repository.repositoryname
        self.priority = self.repository.priority
        self.ntrials = self.repository.ntrials
        self.done = False
        self.status = None 
        self.timestamp = int( time.time() )  # the time this Request object was created


    def __cmp__(self, other):
        '''
        method to sort the request in the PriorityQueue
        '''
        if self.priority < other.priority:
            return 1
        if self.priority > other.priority:
            return -1
        if self.priority == other.priority:
            if self.timestamp < other.timestamp:
                return -1
            if self.timestamp > other.timestamp:
                return 1
            if self.timestamp == other.timestamp:
                return 0


    def run(self):

        self.log.info('running snapshot for repository %s' %self.repositoryname)    
        trial = 1 
        while trial <= self.ntrials:
            self.log.info('attempt %s to snapshot for repository %s' %(trial, self.repositoryname))
            rc = self._run_snapshot()
            if rc == 0: 
                self.log.info('snapshot for repository %s done successfully' %self.repositoryname)
                break
            else:
                self.log.error('attempt %s to snapshot for repository %s failed' %(trial, self.repositoryname))
                if trial < self.ntrials:
                    self._wait_between_trials(trial)
                trial += 1
        else:
            self.log.critical('snapshot for repository %s failed' %self.repositoryname)

        # return latest rc
        return rc
    

    def _wait_between_trials(self, trial):
        '''
        wait some time between attempts
        increasing exponentially between trials
        '''
        waittime = pow(10, trial)
        time.sleep(waittime)


    def _run_snapshot(self):

        self.log.info('attempt to do a snapshot')

        before = time.time()

        cmd = 'cvmfs_server snapshot %s' %self.repositoryname
        #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        #(out, err) = p.communicate()
        #rc = p.returncode
        tcommand = utils.TimeoutCommand(cmd)
        tcommand.run(self.repository.timeout)
        out = tcommand.out
        err = tcommand.err
        rc = tcommand.rc

        self.log.info('out, err and rc from cvmfs_server snapshot command = %s, %s, %s' %(out, err, rc))
        delta = time.time() - before
        self.log.info('It took %s seconds to perform the snapshot for repository %s' %(delta, self.repositoryname))

        return rc

    def setdone(self):
        self.done = True


# =============================================================================
#       CLASS REPLICA REQUEST QUEUE
# =============================================================================

#
# NOTE
#
# if at the end there is no extra needs for this class,
# maybe it can be eliminated and let
# ReplicaManager to have an object 
#       self.replicarequestqueue = Queue.Queue()
#
class ReplicaRequestQueue(Queue.PriorityQueue):
    """
    Pipe where ReplicaRequest objects are being queue'ed.
    """

    def __init__(self):

        Queue.PriorityQueue.__init__(self)
        self.log = logging.getLogger('cvmfsreplica.replicarequestqueue')


# =============================================================================
#       CLASS REPLICA AGENT 
# =============================================================================


class ReplicaAgent(threading.Thread):
    """
    This class gets replica requests from the pipe and
    runs the snapshots.

    There are as many instances of this class 
    as the maximum number of snapshots we want to allow
    to happen simultaneously.
    """

    def __init__(self, manager, index):
        """
        manager is a reference to the ReplicaManager class
        that created object Repository
        It includes needed things like object self.replicarequestqueue
       
        index is just a integer to distiguish one object from another 
        """

        threading.Thread.__init__(self) # init the thread
        self.log = logging.getLogger('cvmfsreplica.replicaagent[%s]' %index)
        self.stopevent = threading.Event()
    
        self.manager = manager
        self.index = index


    def run(self):
        '''
        Method called by thread.start()
        Main functional loop.
        '''
        
        self.log.debug('starting ReplicaAgent thread main loop...')    
        ### FIXME
        ### FAKE IMPLEMENTATION FOR NOW

        while not self.stopevent.isSet():
            time.sleep(1)
            self.log.trace('ReplicaAgent loop') 
            if not self.manager.replicarequestqueue.empty():
                req = self.manager.replicarequestqueue.get()
                self.log.info('got a replica request object for repository %s' %req.repositoryname)
                rc = req.run()
                self.log.info('request processed')
                req.setdone()
                req.status = rc
            


    def join(self,timeout=None):
        '''
        Stop the thread. Overriding this method required to handle Ctrl-C from console.
        '''
        self.stopevent.set()
        self.log.debug('Stopping thread...')
        threading.Thread.join(self, timeout)





