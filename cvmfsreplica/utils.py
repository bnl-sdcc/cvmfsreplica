#!/usr/bin/env python

import calendar
import datetime 
import os
import subprocess
import threading
import time



def date2seconds(date_str):
    '''
    converts a string date into seconds since Epoch

    The string date_str can be either the output of command
        `date`
    or command
        `date -u`
    Threfore, they look like 
        "Fri Apr 15 11:32:19 EDT 2016"
    or
        "Fri Apr 15 15:32:19 UTC 2016"

    Depending on the format of the string (UTC or local),
    we need to use different python packages to convert it.
    
    TO DO: investigate if it can be done in a simpler way
           using package pytz
            http://pytz.sourceforge.net/

    The format of the date_str string can be expressed as
        '%a %b %d %H:%M:%S %Z %Y'
    Explanation can be found in the manpage for command "date",
    or in here
        https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
    '''

    DATE_STR_FORMAT = '%a %b %d %H:%M:%S %Z %Y'
    date_time = datetime.datetime.strptime(date_str, DATE_STR_FORMAT)
    date_struct = date_time.timetuple()

    if 'UTC' in date_str:
        seconds = calendar.timegm(date_struct)
    else:
        seconds = int( time.mktime(date_struct) )

    return seconds


def check_disk_space(dir, minsize):
    '''
    checks if the free space in disk for the partition
    hosting directory "dir" is larger than "minsize".
    minsize is in bytes.
    '''

    stats = os.statvfs(dir)
    free_space = stats.f_frsize * stats.f_bfree
    return free_space > minsize


class TimeoutCommand(object):
    '''
    run a subprocess, with a timeout
    '''
    def __init__(self, cmd):
        self.cmd = cmd
        self.out = None
        self.err = None
        self.rc = None

    def run(self, timeout=None):
        def target():
            self.process = subprocess.Popen(self.cmd,  
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE, 
                                            shell=True
                                           )
            (self.out, self.err) = self.process.communicate()
            self.rc = self.process.returncode

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
            # NOTE: here we can raise an exception


