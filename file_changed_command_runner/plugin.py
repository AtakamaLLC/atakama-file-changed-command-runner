""" Atakama plugin: FileChangedCommandRunner """

import logging
import subprocess
from typing import Dict
from atakama import FileChangedPlugin

from .callback_server import CallbackServer


log = logging.getLogger(__name__)


class FileChangedCommandRunner(FileChangedPlugin):
    """Atakama plugin: FileChangedCommandRunner"""

    DEFAULT_CALLBACK_TIMEOUT: float = 10

    def __init__(self, args: Dict[str, str]):
        super().__init__(args)
        self._cmd: str = args["cmd"]
        self._timeout: float = args.get("timeout", self.DEFAULT_CALLBACK_TIMEOUT)
        self._callback_server: CallbackServer = CallbackServer()

    @staticmethod
    def name():
        return "file-changed-command-runner"

    def file_changed(self, full_path: str) -> None:
        with self._callback_server as cb:
            # TODO: make this platform-agnostic
            cmd = f'"{self._cmd}" "{full_path}" "{cb.url}"'
            log.debug("about to run command: %s", cmd)
            with subprocess.Popen(cmd) as proc:
                log.debug("waiting for callback...")
                cb.wait(self._timeout)
                log.debug(
                    "done waiting: %s", "called" if cb.got_callback else "timed out"
                )
                proc.terminate()
