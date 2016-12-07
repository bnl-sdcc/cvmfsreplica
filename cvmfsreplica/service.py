#!/usr/bin/env python   


__version__ = "0.9.5"

import commands
import datetime
import logging
import logging.handlers
import os
import pwd
import re
import subprocess
import string
import sys
import time
import threading
import traceback

from replicas import ReplicaManager
#from pyconfidence import Config
from cvmfsreplica.pyconfidence import Config
from cvmfsreplica.cvmfsreplicaex import ServiceConfigurationFailure



# =========================================================================
#       CLAS TO ACT AS INTERFACE WITH CLI SCRIPTS 
# =========================================================================


class serviceCLI(object):
    """
    class to manage the threads performing
    the cvmfs snapshots
    """

    def __init__(self, opts):
    
        self.options = opts
    
        try:
            self._readconfigs()
        except Exception, ex:
            raise ServiceConfigurationFailure(ex)


        self._setuplogging()

        self.log.trace('main config file:\n%s' %self.conf)
        self.log.trace('repositories config file:\n%s' %self.repositoriesconf)
 
        self.replica_manager = ReplicaManager(self)

        self.log.debug('object serviceCLI initialized')

    # =========================================================================
    #       READ CONFIG FILES
    # =========================================================================

    def _readconfigs(self):
        """
        read the configuration files:
            1. read the main configuration file, 
               whose path was passed via input option  --conf
            2. from there, get config values, 
               including the path
               to the repositories configuration file
            3. read the repositories configuration file
        """

        # 1
        self.conf = Config()
        self.conf.readfp(open(self.options.conffile))

        # 2
        self._readloggingconfig()
        self._readmaxthreadsconfig()
        repositoriesconffile = self._readrepositoriesconfig()

        # 3
        self.repositoriesconf = Config()
        self.repositoriesconf.readfp(open(repositoriesconffile))


    def _readloggingconfig(self):
        """
        get logging configuration from the config file
        """
        try:
            self.loglevel = self.conf.get("REPLICA", "loglevel")
        except:
            # DEFAULT value
            self.loglevel = "WARNING"
        try:
            self.logtype = self.conf.get("REPLICA", "log")
        except:
            # DEFAULT value
            self.logtype = "file:///var/log/cvmfsreplica/cvmfsreplica.log"


    def _readmaxthreadsconfig(self):
        # FIXME too much duplicated code in these _readXYZ() methods
        """
        get the maximum number of allowed concurrent threads 
        """
        try: 
            self.maxthreads = self.conf.getint("REPLICA", "maximum_concurrent_snapshots")
        except:
            msg = "configuration variable 'maximum_concurrent_snapshots' is not defined. Aborting"
            raise Exception(msg)


    def _readrepositoriesconfig(self):
        """
        get the  configuration file for repositories
        """
        try:
            repositoriesconffile = self.conf.get('REPLICA','repositoriesconf')
            if repositoriesconffile.startswith('file:'):
                repositoriesconffile = repositoriesconffile[7:]
            return repositoriesconffile
        except:
            msg = "configuration variable 'repositoriesconf' is not defined. Aborting"
            raise Exception(msg) 


    # =========================================================================
    #       SET LOGGING
    # =========================================================================

    def _setuplogging(self):

        self._add_trace_level()

        self.log = logging.getLogger('cvmfsreplica')
        
        MESSAGE_FORMAT='%(asctime)s (UTC) - CVMFSREPLICA [ %(levelname)s ] %(name)s %(filename)s:%(lineno)d %(funcName)s(): %(message)s'
        log_formatter = logging.Formatter(MESSAGE_FORMAT)
        log_formatter.converter = time.gmtime  # to convert timestamps to UTC


        # set the logging service
        if self.logtype == "syslog":
            handler = self._getlogginghandler("syslog")
        elif self.logtype == "stdout":
            handler = self._getlogginghandler("stdout")
        else:
            if self.logtype.startswith('file:'):
                filename = self.logtype[7:]
                handler = self._getlogginghandler("file", filename=filename)

        handler.setFormatter(log_formatter)
        self.log.addHandler(handler)

        # set the logging level
        loglevel = logging.getLevelName(self.loglevel)
        self.log.setLevel(loglevel)


    def _add_trace_level(self):

        logging.TRACE = 5
        logging.addLevelName(logging.TRACE, 'TRACE')
        def trace(self, msg, *args, **kwargs):
            self.log(logging.TRACE, msg, *args, **kwargs)
        logging.Logger.trace = trace


    def _getlogginghandler(self, type, filename=None):

        if type == "syslog":
            return logging.handlers.SysLogHandler()

        elif type == "stdout":
            return logging.StreamHandler(sys.stdout)

        elif type == "file":
            return logging.FileHandler(filename)


    # =========================================================================
    #      RUN THE SERVICE 
    # =========================================================================

    def run(self):
        """
        runs the actual service by calling the method start()
        in the library class ReplicaManager.

        It stops everything if a signal is received,
        or some fatal error happens.
        """

        try:
            self.log.info('Starting ReplicaManager object main process...')
            self.replica_manager.run()

        except KeyboardInterrupt:
            self.log.info('Caught keyboard interrupt - exitting')
            self.replica_manager.shutdown()
            sys.exit(0)
        except ImportError, errorMsg:
            self.log.critical('Failed to import necessary python module: %s' % errorMsg)
            sys.exit(1)
        except:
            self.log.critical('Unexpected exception')
            self.log.critical(traceback.format_exc(None))
            print(traceback.format_exc(None))
            sys.exit(1)



