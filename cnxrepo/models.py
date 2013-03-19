# -*- coding: utf-8 -*-
"""Repository specific models"""
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    relationship,
    scoped_session,
    sessionmaker,
    )
from sqlalchemy.event import listens_for as sqlalchemy_listens_for

from zope.sqlalchemy import ZopeTransactionExtension

from .events import notify, ContentAdded


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

internal_resource_associations = Table(
    'internal_resource_associations',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id')),
    Column('resource_id', Integer, ForeignKey('resources.id')),
    )

external_resource_associations = Table(
    'external_resource_associations',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id')),
    Column('resource_id', Integer, ForeignKey('external_resources.id')),
    )


class Resource(Base):
    """Any file resource that is not `Content`."""
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(LargeBinary)

    def __init__(self, name, content):
        self.name = name
        self.content = content


class ExternalResource(Base):
    """Any resource that is not within this system."""
    __tablename__ = 'external_resources'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    uri = Column(String)

    def __init__(self, name, uri):
        self.name = name
        self.uri = uri


class Content(Base):
    """Any text based content"""
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)

    # Resource relationships
    internal_resources = relationship(Resource,
                                      secondary=internal_resource_associations,
                                      backref='used_in')
    external_resources = relationship(ExternalResource,
                                      secondary=external_resource_associations,
                                      backref='used_in')

    def __init__(self, title, content=''):
        self.title = title
        self.content = content
        notify(ContentAdded(self))

@sqlalchemy_listens_for(Content, 'after_insert')
def content_added(mapper, connection, target):
    notify(ContentAdded(target))
