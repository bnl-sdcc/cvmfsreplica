#!/usr/bin/env python

import calendar
import datetime 
import time

import ConfigParser

import cvmfsreplica.pyconfidence
# NOTE:
# to avoid problems due the circular imports
# between modules, we 
#   "import pyconfidence" 
# instead
#   "from pyconfidence import foo" 


class Config(ConfigParser.SafeConfigParser, object):
    """
    custom class to read configuration files,
    and more. 

    Documentation on ConfigParser can be found here:
        https://docs.python.org/2/library/configparser.html
    """

    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)

    def getlist(self, section, option, conv=str):
        '''
        converts the value into a list.
        If needed, converts each item in the list
        '''
        value = super(Config,self).get(section, option)
        return [conv(i.strip()) for i in value.split(',')]


    def getSection(self, section):
        '''
        creates and returns a new Config object, 
        with the content of a single section
        '''
    
        conf = cvmfsreplica.pyconfidence.single.SingleSectionConfig()
        if self.has_section(section):
                #conf.add_section(section)
                for item in self.items(section, raw=True):
                    conf.set(item[0], item[1])
        return conf


    def __str__(self):
        """
        returns a string with the content of the config file.
        Mostly for logging and testing.
        It does not checks type (int, float, boolean),
        just returns a raw string.
        """
        
        out = ''
        for section in self.sections():
            out += '[%s]\n' %section
            for item in self.items(section):
                out += '%s = %s\n' %item
        out = out[:-1]
        return out


