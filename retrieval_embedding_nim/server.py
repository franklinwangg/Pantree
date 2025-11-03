# import os, subprocess, time, sys, urllib.request

# # --- Config ---
# # MODEL = "llama-3.2-nv-embedqa-1b-v2"
# MODEL = "nv-embedqa-e5-v5"


# IMAGE = f"nvcr.io/nim/nvidia/{MODEL}:1.10.0"
# PORT = "8002"
# CACHE = os.path.expanduser("~/.cache/nim")
# API_KEY = os.environ.get("NGC_API_KEY")

# # --- Helper for HTTP check ---
# def http_get(url, timeout=2):
#     try:
#         with urllib.request.urlopen(url, timeout=timeout) as r:
#             return r.read().decode()
#     except Exception:
#         return ""

# # --- Main ---
# if not API_KEY:
#     sys.exit("❌ Set NGC_API_KEY environment variable first.")

# os.makedirs(CACHE, exist_ok=True)

# # 1. Login to nvcr.io
# print("+ docker login nvcr.io -u $oauthtoken --password-stdin")
# p = subprocess.Popen(
#     ["docker", "login", "nvcr.io", "-u", "$oauthtoken", "--password-stdin"],
#     stdin=subprocess.PIPE,
# )
# p.stdin.write(API_KEY.encode()); p.stdin.close()
# if p.wait() != 0:
#     sys.exit("❌ Docker login failed")

# # 2. Pull the NIM image
# print(f"+ docker pull {IMAGE}")
# subprocess.run(["docker", "pull", IMAGE], check=True)

# # 3. Stop any existing container
# print(f"+ docker rm -f {MODEL}")
# subprocess.run(["docker", "rm", "-f", MODEL], check=False)

# # 4. Run the container (localhost:8000 → container:8000)
# print(f"+ docker run -d --rm --name {MODEL} --gpus all --shm-size=16g "
#       f"-e NGC_API_KEY={API_KEY} -p {PORT}:8000 "
#       f"-v {CACHE}:/opt/nim/.cache {IMAGE}")
# subprocess.run([
#     "docker", "run", "-d", "--rm",
#     "--name", MODEL,
#     "--gpus", "all",
#     "--shm-size=16g",
#     "-e", f"NGC_API_KEY={API_KEY}",
#     "-p", f"{PORT}:8000",
#     "-v", f"{CACHE}:/opt/nim/.cache",
#     IMAGE
# ], check=True)

# # 5. Wait for readiness
# url = f"http://localhost:{PORT}/v1/health/ready"
# print(f"⏳ Waiting for NIM to be ready at {url} ...")
# for _ in range(300):  # wait up to 10 min (2s * 300)
#     # if "OK" in http_get(url):
#     #     print(f"✅ NIM is ready at http://localhost:{PORT}")
#     #     break
#     if "ready" in http_get(url).lower():
#         print(f"✅ NIM is ready at http://localhost:{PORT}")
#         break
#     time.sleep(2)
# else:
#     sys.exit("❌ Timed out waiting for readiness.")

# print("➡️ You can now send requests to:")
# print(f"   http://localhost:{PORT}/v1/models/{MODEL}/infer")


import os, subprocess, time, sys, urllib.request

MODEL = "nv-embedqa-e5-v5"
IMAGE = "729386419841.dkr.ecr.us-west-2.amazonaws.com/nv-embedqa-e5-v5:1.10.0"
PORT = "8002"
CACHE = os.path.expanduser("~/.cache/nim")
API_KEY = os.environ.get("NGC_API_KEY")

def http_get(url, timeout=2):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode()
    except Exception:
        return ""

os.makedirs(CACHE, exist_ok=True)

# --- ECR login ---
print("+ aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 729386419841.dkr.ecr.us-west-2.amazonaws.com")
subprocess.run(
    "aws ecr get-login-password --region us-west-2 | "
    "docker login --username AWS --password-stdin 729386419841.dkr.ecr.us-west-2.amazonaws.com",
    shell=True, check=True
)

# --- Pull image ---
print(f"+ docker pull {IMAGE}")
subprocess.run(["docker", "pull", IMAGE], check=True)

# --- Remove old container ---
print(f"+ docker rm -f {MODEL}")
subprocess.run(["docker", "rm", "-f", MODEL], check=False)

# --- Run container ---
print(f"+ docker run -d --rm --name {MODEL} -p {PORT}:8000 -e NGC_API_KEY={API_KEY} {IMAGE}")
# subprocess.run([
#     "docker", "run", "-d", "--rm",
#     "--name", MODEL,
#     "-p", f"{PORT}:8000",
#     "-e", f"NGC_API_KEY={API_KEY}",
#     IMAGE
# ], check=True)
subprocess.run([
    "docker", "run", "-d", "--rm",
    "--gpus", "all",
    "--ipc=host",
    "--ulimit", "memlock=-1",
    "--ulimit", "stack=67108864",
    "--name", MODEL,
    "-p", f"{PORT}:8000",
    "-e", f"NGC_API_KEY={API_KEY}",
    "-v", f"{CACHE}:/opt/nim/.cache",
    IMAGE
], check=True)


# --- Wait for readiness ---
url = f"http://localhost:{PORT}/v1/health/ready"
print(f"⏳ Waiting for NIM to be ready at {url} ...")
for _ in range(300):
    if "ready" in http_get(url).lower():
        print(f"✅ NIM is ready at http://localhost:{PORT}")
        break
    time.sleep(2)
else:
    sys.exit("❌ Timed out waiting for readiness.")

print("➡️ You can now send requests to:")
print(f"   http://localhost:{PORT}/v1/embeddings")
