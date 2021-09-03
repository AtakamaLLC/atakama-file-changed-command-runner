import threading
import pytest
import requests
from unittest.mock import patch
from urllib.parse import urlparse

from file_changed_command_runner.callback_server import CallbackServer


def test_basic():
    cb = CallbackServer()
    assert not cb.allow_reuse_address
    assert not cb._token
    assert cb.server_port in cb.port_range


def test_not_ready():
    cb = CallbackServer()
    with pytest.raises(AssertionError):
        _ = cb.got_callback
    with pytest.raises(AssertionError):
        _ = cb.url
    with pytest.raises(AssertionError):
        cb.wait()


def test_no_ports():
    cb = CallbackServer()
    port_taken = range(cb.server_port, cb.server_port)
    with patch("file_changed_command_runner.callback_server.CallbackServer.port_range", port_taken):
        with pytest.raises(RuntimeError):
            # expect this to raise: the only port in patched port_range is taken
            CallbackServer()


def test_wait_timeout():
    with CallbackServer() as cb:
        cb.wait(timeout=0.1)
        assert not cb.got_callback


def test_process_callback():
    timeout = 3
    listening = threading.Event()
    done = threading.Event()

    with CallbackServer() as cb:

        def waiter():
            listening.set()
            cb.wait(timeout)
            done.set()

        # server is waiting in another thread
        threading.Thread(target=waiter, daemon=True).start()
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


def test_handler():
    timeout = 5
    listening = threading.Event()
    done = threading.Event()
    process = threading.Event()

    with CallbackServer() as cb:

        def waiter():
            listening.set()
            cb.wait(timeout)
            done.set()

        orig_process_callback = cb.process_callback

        def new_process_callback(*args):
            process.set()
            orig_process_callback(*args)

        with patch.object(cb, "process_callback", new_process_callback):

            # server is waiting in another thread
            threading.Thread(target=waiter, daemon=True).start()
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
