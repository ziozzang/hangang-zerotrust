"""Private process-group lifetime holder; never import as a production component."""
import json
import os
import pathlib
import signal
import subprocess
import sys
import time
import threading
import tempfile

def main():
    signal.signal(signal.SIGTERM, lambda *_: None)
    expected_parent = int(sys.argv[1])
    status = pathlib.Path(sys.argv[2])
    def watch_parent():
        while os.getppid() == expected_parent:
            time.sleep(.1)
        # This process is the retained leader of its own session/group. No
        # external PID/name lookup is used, even if the supervisor dies first.
        os.killpg(os.getpgrp(), signal.SIGTERM)
        time.sleep(10)
        os.killpg(os.getpgrp(), signal.SIGKILL)
    threading.Thread(target=watch_parent, daemon=True).start()
    if os.getppid() != expected_parent:
        os.killpg(os.getpgrp(), signal.SIGKILL)
    child = subprocess.Popen(sys.argv[3:])  # Same new session/group as guardian.
    code = child.wait()
    fd, pending = tempfile.mkstemp(prefix='.core-exit-', dir=status.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump({'exit': code}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, status)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)
    # Keep PGID reserved even after the core leader exits. Supervisor sends the
    # group signal BEFORE reaping this process, including if this is a zombie.
    while True:
        signal.pause()

if __name__ == '__main__':
    main()
