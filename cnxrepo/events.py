# -*- coding: utf-8 -*-
"""Application trigger event classes and handlers."""
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
    """Content has been added."""


class ContentModified(BaseEvent):
    """Content has been updated."""
