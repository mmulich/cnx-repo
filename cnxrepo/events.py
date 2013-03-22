# -*- coding: utf-8 -*-
"""Application trigger event classes and handlers."""
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
