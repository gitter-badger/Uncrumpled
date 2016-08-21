'''
    Testing the responses from the core are added to our
    system
'''
import os
import tempfile
import shutil
import asyncio
import pytest
import copy

from uncrumpled.core import Core
from uncrumpled.core import dbapi
from uncrumpled.presenter import requests as req
from uncrumpled.presenter.util import system_base

from util import EasyUncrumpled

class App(EasyUncrumpled):
    pass

class Mixin():
    profile = 'profile'
    program = 'program'
    hotkey = ['f5']
    book = 'book'
    def setup_class(cls):
        cls.tdir = tempfile.mkdtemp()
        cls.app = App()
        cls.event_loop = asyncio.get_event_loop()

    def setup_method(self, func):
        '''create fresh database for each test method'''
        self.app.SYSTEM = copy.deepcopy(system_base)
        self.app.db = os.path.join(self.tdir, func.__name__+'.db')
        try:
            os.remove(self.app.db)
        except FileNotFoundError:
            pass
        dbapi.new_db(self.app.db)

    def teardown_class(cls):
        shutil.rmtree(cls.tdir)
        cls.event_loop.close()

    def run(self, func, *args, **kwargs):
        res = func(*args, **kwargs) # ASYNC
        if len(res) == 1:
            return res[0]
        return res
        # return self.event_loop.run_until_complete(func())


class TestProfile(Mixin):
    # @asyncio.coroutine #ASYNC hmm, do not think this is needed
    def test_profile(self):
        response = self.run(req.profile_create, self.app, profile=self.profile)
        assert 'profile created' in response.lower()

        response = self.run(req.profile_create, self.app, self.profile)
        assert 'profile already in use' in response.lower()

        response = self.run(req.profile_delete, self.app, self.profile)
        assert 'profile deleted' in response.lower()

        response = self.run(req.profile_delete, self.app, self.profile)
        assert 'profile does not exist' in response.lower()


class TestUiInit(Mixin):
    def test_with_first_run_true(self):
        self.app.first_run = True
        response = self.run(req.ui_init, self.app)
        assert 'show_window' in response[0]
        assert 'welcome_screen' in response[1]
        assert 'profile_set_active' in response[2]
        assert 'system_hotkey_register' in response[3]
        assert 'system_hotkey_register' in response[4]

    def test_with_first_run_false(self):
        self.app.first_run = False
        response = self.run(req.ui_init, self.app)
        assert 'profile_set_active' in response


class TestHotkeyPressed(Mixin):
    def test_page_load_and_page_close(s):
        dbapi.profile_create(s.app.db, s.profile)
        kwargs = {'no_process': 'write'}
        dbapi.book_create(s.app.db, s.profile, s.book, s.hotkey, **kwargs)
        resp =s.run(req.hotkey_pressed, s.app, s.profile, s.program, s.hotkey)
        assert 'page_load' in resp

        resp = s.run(req.hotkey_pressed, s.app, s.profile, s.program, s.hotkey)
        assert 'page_close' in resp
