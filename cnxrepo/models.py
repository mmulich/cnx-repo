# -*- coding: utf-8 -*-
"""Repository specific models"""
from lxml import html
from pyramid.events import subscriber
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

from cnxrepo import events


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

internal_reference_associations = Table(
    'internal_reference_associations',
    Base.metadata,
    Column('left_id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('right_id', Integer, ForeignKey('contents.id'), primary_key=True),
    )

external_reference_associations = Table(
    'external_reference_associations',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id')),
    Column('external_reference_id', Integer,
           ForeignKey('external_references.id')),
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
    uri = Column(String, nullable=False, unique=True)

    def __init__(self, uri):
        self.uri = uri


class ExternalReference(Base):
    """An externally referenced piece of content."""
    __tablename__ = 'external_references'
    id = Column(Integer, primary_key=True)
    uri = Column(String, nullable=False, unique=True)

    def __init__(self, uri):
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
    # Reference relationships
    internal_references = relationship(
        'Content',
        secondary=internal_reference_associations,
        primaryjoin=id==internal_reference_associations.c.left_id,
        secondaryjoin=id==internal_reference_associations.c.right_id,
        backref='used_in',
        )
    external_references = relationship(
        ExternalReference,
        secondary=external_reference_associations,
        backref='used_in',
        )

    def __init__(self, title, content=''):
        self.title = title
        self.content = content


@sqlalchemy_listens_for(Content, 'after_insert')
def content_added(mapper, connection, target):
    events.notify(events.ContentAdded(target))

def find_referenced_content(content):
    """Given some html content, yield any referenced content entries."""
    parsed_content = html.fromstring(content)
    # Parse for 'a' tags.
    for ref in parsed_content.xpath('//a/@href'):
        yield ref
    raise StopIteration

def find_resources(content):
    """Given some html content, yield any resource entries."""
    # ??? I'm sure there are better ways to do this, no?
    parsed_content = html.fromstring(content)
    # Parse 'img' tags.
    for uri in parsed_content.xpath('//img/@src'):
        yield uri
    for uri in parsed_content.xpath('//embed/@src'):
        yield uri
    raise StopIteration

def extract_resource_id_from_uri(uri):
    """Extract the resource id from the given URI."""
    # TODO Replace with reverse route parsing after the route has been crated.
    return  uri[len('/resource/'):]

@subscriber(events.ContentAdded)
def catalog_content_references(event):
    """Capture references to other content objects and build a relationship
    entry.

    """
    for ref in find_referenced_content(event.obj.content):
        print(ref)

@subscriber(events.ContentAdded)
def catalog_resources(event):
    """For any resource (internal or external) used in the content object,
    capture its usage to build relationship information.

    Internal resouces will be captured in an association table to build
    a minimal relationship between the content and resource.
    Extneral resources are captured and placed in an external resources
    relation table.

    """
    session = DBSession()
    for uri in find_resources(event.obj.content):
        if uri.startswith('http'):
            # Create an external reference.
            resource = ExternalResource(uri)
            resource.used_in.append(event.obj)
            session.add(resource)
        else:
            # Create a resource reference.
            resource_id = extract_resource_id_from_uri(uri)
            resource = session.query(Resource) \
                .filter(Resource.id==resource_id) \
                .one()
            resource.used_in.append(event.obj)
            session.add(resource)
