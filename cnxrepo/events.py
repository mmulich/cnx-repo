# -*- coding: utf-8 -*-
"""Application trigger event classes and handlers."""
from pyramid.events import subscriber
from pyramid.threadlocal import get_current_registry


def notify(event):
    """Alias to Registry.notify"""
    get_current_registry().notify(event)


class BaseEvent:
    """Base class for any object related events."""
    obj = None

    def __init__(self, obj):
        self.obj = obj


class ContentAdded(BaseEvent):
    """Content has been added to the application."""


@subscriber(ContentAdded)
def catalog_resource(event):
    """For any resource (internal or external) used in the content object,
    capture its usage to build relationship information.

    Internal resouces will be captured in an association table to build
    a minimal relationship between the content and resource.
    Extneral resources are captured and placed in an external resources
    relation table.

    """
    # TODO Parse the content for resource usage. Make relational
    #      entries for the found resources.
    pass
