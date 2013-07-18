# encoding: utf8

# Copyright 2011 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Some tests for the serving part."""

import json

from unittest import TestCase

from mock import patch
from sqlalchemy import create_engine

from kilink import kilink, backend


class FakeRequest(object):
    """A fake request to patch Flask."""
    def __init__(self, **k):
        self.__dict__.update(k)


class ServingTestCase(TestCase):
    """Tests for server."""

    def setUp(self):
        """Set up."""
        super(ServingTestCase, self).setUp()
        engine = create_engine("sqlite://")
        self.backend = backend.KilinkBackend(engine)
        kilink.kilinkbackend = self.backend
        self.app = kilink.app.test_client()

        _ctx = patch("kilink.kilink.render_template")
        self.mocked_render = _ctx.start()
        self.addCleanup(_ctx.stop)

        _ctx = patch("kilink.kilink.redirect")
        self.mocked_redirect = _ctx.start()
        self.addCleanup(_ctx.stop)

    def test_root_page(self):
        """Root page."""
        kilink.index()

        k = {}
        k['value'] = ''
        k['button_text'] = 'Create kilink'
        k['kid_info'] = 'k/'
        k['tree_info'] = []
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_serving_base(self):
        """Serving a kilink, base."""
        klnk = self.backend.create_kilink("content")
        r = self.app.get("/k/%s" % (klnk.kid,))

        tree = [[1, -1, klnk.revno, "/k/%s/%s" % (klnk.kid, klnk.revno),
                str(klnk.timestamp)]]
        k = {}
        k['value'] = 'content'
        k['button_text'] = 'Save new version'
        k['kid_info'] = "k/%s/%s" % (klnk.kid, klnk.revno)
        k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.revno
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_serving_revno(self):
        """Serving a kilink with a revno."""
        klnk = self.backend.create_kilink("content")
        self.app.get("/k/%s/%s" % (klnk.kid, klnk.revno))

        tree = [[1, -1, klnk.revno, "/k/%s/%s" % (klnk.kid, klnk.revno),
                str(klnk.timestamp)]]
        k = {}
        k['value'] = 'content'
        k['button_text'] = 'Save new version'
        k['kid_info'] = "k/%s/%s" % (klnk.kid, klnk.revno)
        k['tree_info'] = json.dumps(tree)
        k['current_revno'] = klnk.revno
        self.mocked_render.assert_called_once_with("_new.html", **k)

    def test_create(self):
        """Create a kilink."""
        self.app.post("/k/", data=dict(content="content"))

        # get what was created, to compare
        session = self.backend.sm.get_session()
        created = session.query(backend.Kilink).one()

        # compare
        url = "/k/%s" % (created.kid,)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_update_base(self):
        """Update a kilink from it's base node."""
        klnk = self.backend.create_kilink("content")

        url = "/k/%s" % (klnk.kid,)
        r = self.app.post(url, data=dict(content=u"moño"))

        # get what was created, to compare
        session = self.backend.sm.get_session()
        created = session.query(backend.Kilink).filter_by(
            kid=klnk.kid, parent=klnk.revno).one()

        # compare
        url = "/k/%s/%s" % (created.kid, created.revno)
        self.mocked_redirect.assert_called_once_with(url, code=303)

    def test_update_revno(self):
        """Update a kilink from it's base node."""
        klnk = self.backend.create_kilink("content")
        klnk = self.backend.update_kilink(klnk.kid, klnk.revno, "content2")

        url = "/k/%s/%s" % (klnk.kid, klnk.revno)
        r = self.app.post(url, data=dict(content=u"moño"))

        # get what was created, to compare
        session = self.backend.sm.get_session()
        created = session.query(backend.Kilink).filter_by(
            kid=klnk.kid, parent=klnk.revno).one()

        # compare
        url = "/k/%s/%s" % (created.kid, created.revno)
        self.mocked_redirect.assert_called_once_with(url, code=303)
