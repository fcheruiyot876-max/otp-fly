import os, tempfile, time, threading, shutil
LOG_PATH = tempfile.mkdtemp(prefix='/dev/shm/')
def log(msg):
    with open(os.path.join(LOG_PATH, 'l'), 'a') as f:
        f.write(f"{time.time()}|{msg}\n")
def wipe():
    while True:
        time.sleep(60)
        shutil.rmtree(LOG_PATH, ignore_errors=True)
        os.mkdir(LOG_PATH)
threading.Thread(target=wipe, daemon=True).start()
