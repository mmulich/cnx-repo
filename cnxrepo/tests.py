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
    from .models import DBSession, Base
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    # Now the DBSession can be used as usual.

def test():
    _acquire_sql_session()
    for func in [f for n, f in globals().items() if n.startswith('check')]:
        with testing.testConfig() as config:
            yield func, config
        transaction.abort()

def check_content_added_resource_subscriber(config):
    # Configure the event subscriber in question.
    from .models import catalog_resources_on_add
    config.add_subscriber(catalog_resources_on_add)
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
    config.add_subscriber(catalog_content_references_on_add)
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
