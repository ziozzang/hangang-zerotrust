"""Reuse the qualified counted backend; no auth authority or content logging."""
import pathlib
import sys
import threading
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'native-human-runtime'))
import counted_backend as qualified

class Backend:
    def __init__(self,root,credential):
        if not isinstance(credential,bytes) or not credential.startswith(b'Bearer ') or len(credential)>4096:
            raise ValueError('exact_bearer_header_bytes')
        self.root=pathlib.Path(root);self.root.mkdir(mode=0o700)
        self.counter=qualified.Counter(self.root/'counter.json','authorization',credential)
        self.server=qualified.Server(self.counter)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.origin='http://127.0.0.1:'+str(self.server.server_port)

    def snapshot(self):return self.counter.snapshot()

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
        if self.thread.is_alive():raise RuntimeError('backend_cleanup')
