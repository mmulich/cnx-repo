# -*- coding: utf-8 -*-
"""Application tests"""
import os
import transaction
from nose import with_setup
from pyramid import testing
from pyramid.paster import get_appsettings


HERE = os.path.abspath(os.path.dirname(__file__))
TEST_RESOURCE_FILENAME = 'test-resource.png'
with open(os.path.join(HERE, TEST_RESOURCE_FILENAME), 'rb') as f:
    TEST_RESOURCE_DATA = f.read()

def _acquire_sql_session():
    """Acquire a live SQL session to the actual database implementation."""
    # Grab the SQL DB settings to initialze the SQLAlchemy engine.
    # XXX Obtaining the configuration setting for the SQL DB is
    #     currently evil and MUST be changed in the future.
    try:
        config_file = os.environ['PYRAMID_INI']
    except KeyError:
        raise RuntimeError("Missing PYRAMID_INI environment variable.")
    settings = get_appsettings(config_file)

    # Initialize the Session.
    from sqlalchemy import engine_from_config
    from sqlalchemy.orm import scoped_session, sessionmaker
    from zope.sqlalchemy import ZopeTransactionExtension
    from cnxrepo import models
    models.DBSession = scoped_session(
        sessionmaker(extension=ZopeTransactionExtension(),
                     # In order to easily ref previously created
                     #   objects, we will not expire the session on a
                     #   transaction.commit().
                     expire_on_commit=False)
        )
    engine = engine_from_config(settings, 'sqlalchemy.')
    models.DBSession.configure(bind=engine)
    models.Base.metadata.create_all(engine)
    # Now the DBSession can be used as usual.

def test():
    _acquire_sql_session()
    for func in [f for n, f in globals().items() if n.startswith('check')]:
        with testing.testConfig() as config:
            yield func, config
        testing.tearDown()
        transaction.abort()

def check_content_added_resource_subscriber(config):
    # Configure the event subscriber in question.
    from .models import catalog_resources_on_add
    from .interfaces import IContentAdded
    config.add_subscriber(catalog_resources_on_add, IContentAdded)
    # Create a DB session to work with.
    from .models import DBSession
    session = DBSession()
    # Make some content...
    from .models import Content, Resource
    resource = Resource(TEST_RESOURCE_FILENAME, TEST_RESOURCE_DATA)
    session.add(resource)
    session.flush()  # Flush to get an id for the resource.
    external_resource_uri = 'http://example.com/play-physics.swf'
    content_body = 'Content <img src="/resource/{}" /> Content' \
                   '<embed src="{}"></embed>'.format(resource.id,
                                             external_resource_uri)
    content = Content('Content Title', content_body)
    session.add(content)
    session.flush()

    # Now verify the relationships were created using the relationship
    #   properties on the objects.
    assert content in resource.used_in
    assert resource in content.internal_resources
    from .models import ExternalResource
    external_resource = session.query(ExternalResource).one()
    assert content in external_resource.used_in
    assert external_resource in content.external_resources

def check_content_added_reference_subscriber(config):
    # Configure the event subscriber in question.
    from .models import catalog_content_references_on_add
    from .interfaces import IContentAdded
    config.add_subscriber(catalog_content_references_on_add, IContentAdded)
    # Create a DB session to work with.
    from .models import DBSession
    session = DBSession()
    # Make some content...
    from .models import Content
    content_one = Content('One', 'Content One')
    content_two = Content('Two', 'Content Two')
    session.add_all([content_one, content_two])
    session.flush()
    # And now add a piece of content that references other content.
    external_reference_uri = 'http://example.com/blah.html'
    content_body = '<a href="/content/{}">one</a>' \
                   '<a href="/content/{}">two</a>' \
                   '<a href="{}">blah</a>' \
                   .format(content_one.id, content_two.id,
                           external_reference_uri)
    content = Content('Three', content_body)
    session.add(content)
    session.flush()

    # Now verify the relationships were created using the relationship
    #   properties on the objects.
    assert content_one in content.internal_references
    assert content_two in content.internal_references
    from .models import ExternalReference
    external_reference = session.query(ExternalReference).one()
    assert content in external_reference.used_in
    assert external_reference in content.external_references

# def check_race_condition_w_content_before_resource(config):
#     pass

def check_content_modified_resource_subscriber(config):
    # Configure the event subscriber in question.
    from .models import catalog_resources_on_modify
    from .interfaces import IContentModified
    config.add_subscriber(catalog_resources_on_modify, IContentModified)
    # Create a DB session to work with.
    from .models import DBSession
    session = DBSession()
    # Make some content...
    from .models import Content, Resource
    resource = Resource(TEST_RESOURCE_FILENAME, TEST_RESOURCE_DATA)
    session.add(resource)
    session.flush()  # Flush to get an id for the resource.
    external_resource_uri = 'http://example.com/play-physics.swf'
    content_body = 'Content <img src="/resource/{}" /> Content' \
                   '<embed src="{}"></embed>'.format(resource.id,
                                             external_resource_uri)
    content = Content('Content Title', content_body)
    session.add(content)
    session.flush()
    # Make the modification.
    resource_two = Resource(TEST_RESOURCE_FILENAME, TEST_RESOURCE_DATA)
    session.add(resource_two)
    session.flush()
    external_resource_uri_two = 'http://example.com/play-biology.swf'
    content_body = 'Content <img src="/resource/{}" /> Content' \
        '<embed src="{}"></embed>'.format(resource_two.id,
                                          external_resource_uri_two)
    content.contents = content_body
    session.add(content)
    transaction.commit()

    # Now verify the relationships were created and removed
    #   using the relationship properties on the objects.
    # Internal resources do not get removed, only unreferenced.
    session.merge(content)
    session.merge(resource)
    session.merge(resource_two)
    assert content not in resource.used_in
    assert resource not in content.internal_resources
    assert content in resource_two.used_in
    assert resource_two in content.internal_resources
    # External resources are removed when not in use.
    from .models import ExternalResource
    external_resources = session.query(ExternalResource).all()
    assert len(external_resources) == 1
    external_resource = external_resources[0]
    assert external_resource.uri == external_resource_uri_two
    assert content in external_resources.used_in
    assert external_resource in content.external_resources
