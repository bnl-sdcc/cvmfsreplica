#!/usr/bin/env python

import logging
log = logging.getLogger('cvmfsreplica.plugindispatcher')

###class PluginDispatcher(object):
###
###    def __init__(self, repository):
###
###        self.log = logging.getLogger('cvmfsreplica.plugindispatcher')
###        self.repository = repository
###        self.log.debug('PluginDispatcher object initialized')
###
###
###    def getplugin(self, action, name):
###        '''
###        action is the type of plugin to be delivered
###        name is the actual plugin to be delivered
###        '''
###
###        self.log.debug('Starting for action %s' %action)
###   
###        plugin_path = 'cvmfsreplica.plugins.%s.%s' %(action, name)
###        plugin_module = __import__(plugin_path,
###                                   globals(),
###                                   locals(),
###                                   name 
###                                   )
###        plugin_class = getattr(plugin_module, name) # name of the class is the same as the module
###        return plugin_class



def readplugins(parent, level, type, conf):
    '''
    generic function to instantiate a list of plugins for each type.
    parent is a reference to the object that calls this function
    level is layer in the tree directory. For example: "repository", "service"
    type is the kind of plugin. For example: "report", "acceptance", "post"
    conf is a SingleSectionConfig() object containing the list of plugins of a given type
    '''
    plugins = []
    try:
        option= '%splugins' %type
        # options in conf object are like
        #   reportplugins
        #   acceptanceplugins
        #   postplugins
        if not conf.has_option(option) or\
            conf.get(option) == 'None': #FIXME do this in pyconfidence
               log.trace('no %s plugin' %type)
        else:
            pluginnames = conf.get(option)
            for pluginname in pluginnames.split(','):
                pluginname = pluginname.strip()
                plugin = getplugin(level, type, pluginname)(parent, conf)
                plugins.append(plugin)
        return plugins
    except Exception, ex:
        log.error('Exception captured: %s' %ex)
        log.error('no %s plugin' %type)
        raise ex


def getplugin(level, action, name):
    '''
    level is the high-level type of plugin: repository or service
    action is the type of plugin to be delivered
    name is the actual plugin to be delivered
    '''

    log.debug('Starting for level=%s, action=%s, name=%s' %(level, action, name))

    plugin_path = 'cvmfsreplica.plugins.%s.%s.%s' %(level, action, name)
    try:
        plugin_module = __import__(plugin_path,
                               globals(),
                               locals(),
                               name 
                               )
    except Exception, ex:
        log.debug(ex)

    plugin_class = getattr(plugin_module, name) # name of the class is the same as the module
    log.debug('return plugin %s.%s.%s' %(level, action, name))
    return plugin_class
