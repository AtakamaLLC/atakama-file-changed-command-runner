import pytest
import requests
from threading import Thread, Event
from urllib.parse import urlparse

from file_changed_command_runner.callback_server import CallbackServer


def test_basic():
    cb = CallbackServer()
    assert not cb.allow_reuse_address
    assert not cb._token
    assert cb.server_port


def test_not_ready():
    cb = CallbackServer()
    with pytest.raises(AssertionError):
        _ = cb.got_callback
    with pytest.raises(AssertionError):
        _ = cb.url
    with pytest.raises(AssertionError):
        cb.wait()


def test_wait_timeout():
    with CallbackServer() as cb:
        cb.wait(timeout=0.1)
        assert not cb.got_callback


def test_process_callback():
    timeout = 3
    listening = Event()
    done = Event()

    with CallbackServer() as cb:

        def waiter():
            listening.set()
            cb.wait(timeout)
            done.set()

        # server is waiting in another thread
        Thread(target=waiter, daemon=True).start()
        listening.wait(timeout)
        assert listening.is_set()
        assert cb.url
        assert not cb.got_callback
        assert not done.is_set()

        # fake callback with bad token: still waiting
        cb.process_callback("bad-token")
        assert cb.url
        assert not cb.got_callback
        assert not done.is_set()

        # fake callback with good token: wait() returns
        token = urlparse(cb.url).path.lstrip("/")
        cb.process_callback(token)
        done.wait(timeout)
        assert done.is_set()
        assert cb.got_callback


def _do_callback_requests(cb: CallbackServer, listening: Event, done: Event, process: Event):
    timeout = 5

    with cb:

        def waiter():
            listening.set()
            cb.wait(timeout)
            done.set()

        # server is waiting in another thread
        Thread(target=waiter, daemon=True).start()
        listening.wait(timeout)
        assert listening.is_set()
        assert cb.url
        assert not cb.got_callback
        assert not done.is_set()

        # real callback with the wrong url: still waiting
        requests.request("GET", cb.url + "x")
        process.wait(timeout)
        assert process.is_set()
        assert not cb.got_callback
        assert not done.is_set()

        # real callback with the right url: wait() returns
        requests.request("GET", cb.url)
        done.wait(timeout)
        assert done.is_set()
        assert cb.got_callback


def test_handler():
    listening = Event()
    done = Event()
    process = Event()

    class TestCallbackServer(CallbackServer):
        def process_callback(self, token: str):
            process.set()
            super().process_callback(token)

    cb = TestCallbackServer()

    _do_callback_requests(cb, listening, done, process)

    # ensure a CallbackServer instance can be reused
    listening.clear()
    done.clear()
    process.clear()
    _do_callback_requests(cb, listening, done, process)
