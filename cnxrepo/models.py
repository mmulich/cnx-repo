# -*- coding: utf-8 -*-
"""Repository specific models"""
from sqlalchemy import (
    Column,
    Integer,
    LargeBinary,
    String,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Content(Base):
    """Any text based content"""
    __tablename__ = 'content'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)

    def __init__(self, title, content=''):
        self.title = title
        self.content = content


class Resource(Base):
    """Any file resource that is not `Content`."""
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(LargeBinary)

    def __init__(self, name, content):
        self.name = name
        self.content = content
