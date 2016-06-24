#!/usr/bin/env python

import calendar
import datetime 
import time

import cvmfsreplica.pyconfidence
# NOTE:
# to avoid problems due the circular imports
# between modules, we 
#   "import pyconfidence" 
# instead
#   "from pyconfidence import foo" 


class SingleSectionConfig(object):

    def __init__(self):
        self.conf = cvmfsreplica.pyconfidence.config.Config()
        self.section = 'singlesection'
        self.conf.add_section(self.section)

    def readfp(self, fp, filename=None):
        self.conf.readfp(fp, filename)
        self.section = self.conf.sections()[0]

    def _get(self, conv, option):
        # reason to re-implement method _get()
        # is that otherwise getint() and getfloat()
        # would call RawConfigParser._get(),
        # that requires 'section' as first argument
        return conv(self.get(option))

    def get(self, option, raw=False, vars=None):
        return self.conf.get(self.section, option, raw, vars)

    def getint(self, option):
        return self._get(int, option)

    def getfloat(self, option):
        return self._get(float, option)

    def getlist(self, option, conv=str):
        return self.conf.getlist(self.section, option, conv)

    def getboolean(self, option):
        v = self.get(option)
        if v.lower() not in self._boolean_states:
            raise ValueError, 'Not a boolean: %s' % v
        return self._boolean_states[v.lower()]

    def items(self, raw=False, vars=None):
        return self.conf.items(self.section, raw, vars)

    def has_option(self, option):
        return self.conf.has_option(self.section, option)

    #def setsection(self, section):
    #    '''
    #    changes the section name from the default 
    #    '''
    #    self.section = section
    

    #def add_section(self, section):
    #    ''' 
    #    method overridden. 
    #    The section name is changed, no section is added.
    #    ''' 
    #    self.section = section

    def set(self, option, value):
        return self.conf.set(self.section, option, value)

    def ascii(self, fp, delimiter='='):
        """
        to read a config file from a bash file with no sections
        """
        # NOTE:
        # there are other implementations. For example:
        #       http://stackoverflow.com/questions/2819696/parsing-properties-file-in-python/2819788#2819788
        # but this one allows for different delimiters
        # 
        for line in fp.readlines():
            line = line[:-1]
            if '#' in line:
                line = line.split('#')[0]
                line.strip()
            if line:
                fields = line.split(delimiter)
                self.set(fields[0].strip(), fields[1].strip())

    def conf2args(self):
        ''' 
        converts all items in the config file
        into a list of strings digestable by argparse
        ''' 
        # FIXME: it assumes all options are long-format,
        #        so it always add double dash --
        args = []
        for i in self.items():
            args.append('--%s'%i[0])
            args.append(i[1])
        return args
 
    def args2conf(self, args):
        '''
        converts a list of strings as the one
        returned by sys.argv into a SingleSectionConfig object
        '''
        #FIXME
        # it assumes that args is a perfect list
        # like ['--foo','bar','-x','0']
        # with always a even number of items,
        # always being option-value pairs.
        # Code should always verify that is correct,
        # and raise an Exception otherwise

        for i in range(len(args)/2):
            option = args[2*i]
            # remove the dashes
            while option[0]=='-':  
                option=option[1:]
            value = args[2*i+1]
            self.set(option, value)

    def namespace(self, name, replace=None, exclude=False):
        '''
        creates a new SingleSectionConfig object
        where string <name> has been stripped from the 
        beginning of options, when present.
        If replace is provided, it substitutes string <name>
        If exclude is True, other (option, value) pairs are ignored.
        If exclude is False, other (option, value) pairs are also included.
        '''
        new_conf = SingleSectionConfig()
        # FIXME new_conf.conf has a different section name than self.conf

        items = self.items()

        # 1st, let's deal with the other options
        # if needed
        # reason is that this way, and option,key pair
        # can be overriden if another one becomes the same after
        # namespace manipulation
        if not exclude:
            for option, value in items:
                if not option.startswith(name):
                    new_conf.set(option, value)
 
        # 2nd, deal with options that are expected to change
        for option, value in items:
            if option.startswith(name):
                option = option[len(name):]
                if replace:
                    option = '%s%s' %(replace, option)
                new_conf.set(option, value)

        return new_conf
