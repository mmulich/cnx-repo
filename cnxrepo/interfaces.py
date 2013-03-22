# -*- coding: utf-8 -*-
from zope.interface import (
    Attribute,
    Interface,
    )


class IContentAdded(Interface):
    """Event triggered on content addition."""
    obj = Attribute("The created object")


class IContentModified(Interface):
    """Event triggered on content modification."""
    obj = Attribute("The modified object")
