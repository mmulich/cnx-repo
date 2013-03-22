# -*- coding: utf-8 -*-
"""Application trigger event classes and handlers.

Greenlets are (/need to be) set up in such a way that they mimic
the transaction manager used in the request process. This is done using
the ``coroutine`` decorator which will initialize a custom Greenlet class that
sets up a new session (via the transaction manager)
and in effect makes it transparent that we have even left the original
process.

The custom events defined in this module have been designed in such a way that
they will lookup the SQLAlchemy model object originally handed to the event
after the coroutine (and therefore using the new session) has been invoked.
This avoids any DetachedInstanceErrors from being raised.

"""
from zope.interface import implementer
from pyramid.threadlocal import get_current_registry

from .interfaces import IContentAdded, IContentModified

def notify(event):
    """Alias to Registry.notify"""
    get_current_registry().notify(event)


class BaseEvent:
    """Base class for any object related events."""
    obj = None

    def __init__(self, obj):
        self.obj = obj


@implementer(IContentAdded)
class ContentAdded:
    """Content has been added."""
    obj = None

    def __init__(self, obj):
        self.obj = obj


@implementer(IContentModified)
class ContentModified:
    """Content has been updated."""
    obj = None

    def __init__(self, obj):
        self.obj = obj
