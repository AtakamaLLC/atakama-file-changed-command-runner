import logging
import os
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler


log = logging.getLogger(__name__)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200, "OK")
        self.end_headers()
        self.close_connection = True  # pylint: disable=attribute-defined-outside-init

        self.server: "CallbackServer"
        self.server.process_callback(self.path.lstrip("/"))


class CallbackServer(HTTPServer):
    """Listens on localhost for a request with a specific token"""

    port_range = range(50000, 51000)

    def __init__(self):
        self.allow_reuse_address: bool = False
        self._token: str = ""
        self._event: threading.Event = threading.Event()

        for port in self.port_range:
            try:
                super().__init__(("localhost", port), CallbackHandler)
                log.info("Listening on localhost:%s", self.server_port)
                break
            except OSError:
                # occurs when a given port is unavailable
                pass

        if not hasattr(self, "server_port"):
            raise RuntimeError("Failed to bind to a localhost port")

        threading.Thread(target=self.serve_forever, daemon=True).start()

    def __enter__(self) -> "CallbackServer":
        self._event.clear()
        self._token = os.urandom(16).hex()
        return self

    def __exit__(self, *args):
        self._token = ""

    @property
    def got_callback(self) -> bool:
        assert self._token
        return self._event.is_set()

    @property
    def url(self) -> str:
        assert self._token
        return f"http://localhost:{self.server_port}/{self._token}"

    def wait(self, timeout: float = None):
        assert self._token
        self._event.wait(timeout=timeout)

    def process_callback(self, token: str):
        if self._token and self._token == token:
            self._event.set()
