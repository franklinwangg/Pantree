import subprocess, time, os, requests

class RetrievalEmbeddingNIMManager:
    def __init__(self, model="nvidia/llama-3.2-nv-embedqa-1b-v2", version="1.10.0", port=8000):
        self.model = model
        self.version = version
        self.port = port
        self.container = model.split("/")[-1]
        self.image = f"nvcr.io/nim/nvidia/{self.container}:{version}"

    def is_running(self):
        try:
            r = requests.get(f"http://localhost:{self.port}/v1/health/ready", timeout=2)
            return r.status_code == 200
        except:
            return False

    def start(self):
        if self.is_running():
            print("✅ NIM already running")
            return
        print("🚀 Starting NIM container...")
        cmd = [
            "docker", "run", "-d", "--rm",
            "--name", self.container,
            "--gpus", "all", "--shm-size=16GB",
            "-e", f"NGC_API_KEY={os.getenv('NGC_API_KEY')}",
            "-v", f"{os.path.expanduser('~/.cache/nim')}:/opt/nim/.cache",
            "-p", f"{self.port}:8000",
            self.image
        ]
        subprocess.run(cmd, check=True)
        for _ in range(60):
            if self.is_running():
                print("✅ NIM is live")
                return
            time.sleep(2)
        raise RuntimeError("❌ NIM failed to start.")
