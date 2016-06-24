#!/usr/bin/env python

import logging
import smtplib
import socket
import time
try:
    from email.mime.text import MIMEText
except:
    from email.MIMEText import MIMEText

from cvmfsreplica.cvmfsreplicaex import PluginConfigurationFailure
from cvmfsreplica.interfaces import RepositoryPluginReportInterface



class Email(RepositoryPluginReportInterface):

    def __init__(self, repository, conf):
        self.log = logging.getLogger('cvmfsreplica.email')
        self.repository = repository
        self.conf = conf
        try:
            self._readadminemail()
            self._readsmtpserver()
        except:
            raise PluginConfigurationFailure('failed to initialize Email plugin')
    
        self.log.debug('plugin Email initialized properly')


    def _readadminemail(self):
        # FIXME too much duplicated code in these _readXYZ() methods
        """
        get the sys admin email address to send notifications 
        """
        try: 
            self.adminemail = self.conf.get("report.email.admin_email")
        except:
            # we use print so this messages goes to the stdout
            msg = "configuration variable 'admin_email' is not defined. Plugin Email cannot be created"
            self.log.error(msg)
            raise PluginConfigurationFailure(msg)
    

    def _readsmtpserver(self):
        # FIXME too much duplicated code in these _readXYZ() methods
        """
        get the email server host to send notifications 
        """
        try: 
            self.smtpserver = self.conf.get("report.email.smtp_server")
        except:
            # we use print so this messages goes to the stdout
            msg = "configuration variable 'smtp_server' is not defined. Plugin Email cannot be created"
            self.log.error(msg)
            raise PluginConfigurationFailure(msg)

    def notifyfailure(self, custommsg=None):
        '''
        if configured for that, 
        sends an email to the sys admin when things go wrong
        '''

        message = "ALERT: CVMFS replica failed\n" 
        message += "repository: %s\n" %self.repository.repositoryname
        message += "time: %s\n" %int(time.time())
        if custommsg:
            message += "%s\n" %custommsg
        message += 'Log files should contain more information.\n'
        msg = MIMEText(message)
        msg['Subject'] = "ALERT: CVMFS replica failed" 
        host = socket.gethostname()
        email_from = "root@%s" %host
        msg['From'] = email_from
        msg['To'] = self.adminemail
        tolist = self.adminemail.split(",")
        
        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(self.smtpserver)
        self.log.info("Sending email: %s" % msg.as_string())
        s.sendmail(email_from , tolist , msg.as_string())
        s.quit()

    def notifysuccess(self):
        # we do not send email just to say it worked
        # at least for now
        pass


