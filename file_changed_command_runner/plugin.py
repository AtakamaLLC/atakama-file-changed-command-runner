""" Atakama plugin: FileChangedCommandRunner """

import logging
import shlex
import subprocess
from typing import Dict
from atakama import FileChangedPlugin

from .callback_server import CallbackServer


log = logging.getLogger(__name__)


class FileChangedCommandRunner(FileChangedPlugin):
    """Atakama plugin: FileChangedCommandRunner"""

    def __init__(self, args: Dict[str, str]):
        super().__init__(args)
        self._cmd: str = args["cmd"]
        self._timeout: float = args.get("timeout", 10)
        self._callback_server: CallbackServer = CallbackServer()

    @staticmethod
    def name():
        return "file-changed-command-runner"

    def file_changed(self, full_path: str) -> None:
        with self._callback_server as cb:
            cmd = f"{shlex.quote(self._cmd)} {shlex.quote(full_path)} {shlex.quote(cb.url)}"
            log.debug("about to run command: %s", cmd)
            with subprocess.Popen(cmd) as proc:
                log.debug("waiting for callback...")
                cb.wait(self._timeout)
                log.debug(
                    "done waiting: %s", "called" if cb.got_callback else "timed out"
                )
                proc.terminate()
