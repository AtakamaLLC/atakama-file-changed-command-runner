import threading
from unittest.mock import patch, MagicMock

from file_changed_command_runner.plugin import FileChangedCommandRunner


plugin_args = {"cmd": "call-me.exe", "timeout": 0.1}


def test_basic():
    fccr = FileChangedCommandRunner(plugin_args)
    assert fccr._cmd == plugin_args["cmd"]
    assert fccr._timeout == plugin_args["timeout"]
    assert fccr.name() == "file-changed-command-runner"


def test_file_changed():
    popen_init_called = False
    popen_terminate_called = False
    changed_path = "/some/path"
    fccr = FileChangedCommandRunner(plugin_args)

    class MockPopen:
        def __init__(*args, **kwargs):
            nonlocal popen_init_called
            popen_init_called = True
            expected_cmd = f"{plugin_args['cmd']} {changed_path} {fccr._callback_server.url}"
            assert args[1] == expected_cmd

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def terminate(self):
            nonlocal popen_terminate_called
            popen_terminate_called = True

    with patch("file_changed_command_runner.plugin.subprocess.Popen", MockPopen):
        fccr.file_changed(changed_path)
        assert popen_init_called
        assert popen_terminate_called
