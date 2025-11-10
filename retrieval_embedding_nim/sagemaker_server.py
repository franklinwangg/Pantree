"""
Deploys an NVIDIA NIM container (e.g., nv-embedqa-e5-v5) as a managed
AWS SageMaker inference endpoint using parameters from a .env file.
If an endpoint with the same name already exists, it is deleted first.
"""

import os
import logging

from dotenv import load_dotenv
import sagemaker
from sagemaker.model import Model
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
# sagemaker.logging_config.configure_logger()

# ---------------------------------------------------------------------
# 1. Load config from .env
# ---------------------------------------------------------------------
load_dotenv()

MODEL_NAME      = os.getenv("MODEL", "nv-embedqa-e5-v5")
IMAGE_TAG       = os.getenv("IMAGE_TAG", "1.10.0")
AWS_REGION      = os.getenv("AWS_REGION", "us-west-2")
ROLE_ARN        = os.getenv("SAGEMAKER_ROLE_ARN")
NGC_API_KEY     = os.getenv("NGC_API_KEY")
INSTANCE_TYPE   = os.getenv("INSTANCE_TYPE", "ml.g4dn.xlarge")
INSTANCE_COUNT  = int(os.getenv("INSTANCE_COUNT", "1"))
ENDPOINT_NAME   = f"{MODEL_NAME}-endpoint"

IMAGE_URI = f"729386419841.dkr.ecr.us-west-2.amazonaws.com/{MODEL_NAME}:{IMAGE_TAG}"

# ---------------------------------------------------------------------
# 2. Validate configuration
# ---------------------------------------------------------------------
if not ROLE_ARN:
    raise ValueError("❌ Missing SAGEMAKER_ROLE_ARN in .env")
if not NGC_API_KEY:
    raise ValueError("❌ Missing NGC_API_KEY in .env")

print(f"🚀 Deploying {MODEL_NAME} to SageMaker ({AWS_REGION})")
print(f"   Image URI: {IMAGE_URI}")
print(f"   Endpoint name: {ENDPOINT_NAME}")
print(f"   Instance type: {INSTANCE_TYPE}")

# ---------------------------------------------------------------------
# 3. Initialize SageMaker + boto3 clients
# ---------------------------------------------------------------------
session = sagemaker.Session(
    boto_session=boto3.Session(profile_name="personal", region_name=AWS_REGION)
)
sm_client = session.sagemaker_client

print(f"📍 SageMaker session region: {session.boto_region_name}")

# ---------------------------------------------------------------------
# 4. Clean up any existing endpoint/config with the same name
# ---------------------------------------------------------------------
def safe_delete_endpoint_and_config(endpoint_name):
    try:
        print(f"🧹 Checking for existing endpoint: {endpoint_name}")
        sm_client.delete_endpoint(EndpointName=endpoint_name)
        print(f"   ⏳ Deleting old endpoint...")
    except ClientError as e:
        if "Could not find endpoint" in str(e):
            print("   ✅ No existing endpoint found.")
        else:
            print(f"   ⚠️ Skipping endpoint delete: {e}")

    try:
        sm_client.delete_endpoint_config(EndpointConfigName=endpoint_name)
        print(f"   ⏳ Deleting old endpoint configuration...")
    except ClientError as e:
        if "Could not find endpoint configuration" in str(e):
            print("   ✅ No existing endpoint config found.")
        else:
            print(f"   ⚠️ Skipping endpoint config delete: {e}")

safe_delete_endpoint_and_config(ENDPOINT_NAME)

# ---------------------------------------------------------------------
# 5. Create and deploy model
# ---------------------------------------------------------------------
# model = Model(
#     image_uri=IMAGE_URI,
#     role=ROLE_ARN,
#     name=MODEL_NAME,
#     env={"NGC_API_KEY": NGC_API_KEY},
#     sagemaker_session=session,
# )
model = Model(
    image_uri="729386419841.dkr.ecr.us-west-2.amazonaws.com/nv-embedqa-e5-v5:1.10.0",
    role=ROLE_ARN,
    name="nv-embedqa-e5-v5",
    env={
        "NGC_API_KEY": NGC_API_KEY,
        "NVIDIA_API_KEY": NGC_API_KEY,
        "NVIDIA_TRITON_SERVER_ENABLE_GPU": "true",
        "NVIDIA_TRITON_SERVER_HTTP_PORT": "8080",
        "NVIDIA_VISIBLE_DEVICES": "all",
        "LOG_LEVEL": "INFO"
    },
    sagemaker_session=session,
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.4xlarge",
    endpoint_name="nv-embedqa-e5-v5-endpoint",
    wait=True,
    container_startup_health_check_timeout=600,
)


print("\n✅ Deployment complete!")
print(f"Your SageMaker endpoint name: {ENDPOINT_NAME}")
print("Use boto3 or SageMaker Runtime to send requests:")

print(f"""
Example:
---------
import boto3, json
runtime = boto3.client('sagemaker-runtime', region_name='{AWS_REGION}')
payload = json.dumps({{
    "model": "nvidia/{MODEL_NAME}",
    "input": ["hello world"]
}})
response = runtime.invoke_endpoint(
    EndpointName="{ENDPOINT_NAME}",
    Body=payload,
    ContentType="application/json"
)
print(response['Body'].read().decode())
""")
