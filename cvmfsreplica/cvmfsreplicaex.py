#! /usr/bin/env python
#
# exception classes for cvmfsreplica project


class ServiceConfigurationFailure(Exception):
    """
    Exception to be raised when basic service configuration
    cannot be read
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RepositoriesConfigurationFailure(Exception):
    """
    Exception to be raised when basic repositories configuration
    cannot be read
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class PluginConfigurationFailure(Exception):
    """
    Exception to be raised when a plugin configuration
    cannot be read
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class AcceptancePluginFailed(Exception):
    """
    Exception to be raised when an Acceptance Plugin
    failed and it has an attribute should_abort = True
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
