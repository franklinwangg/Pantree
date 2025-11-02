"""
Deploys an NVIDIA NIM container (e.g., nv-embedqa-e5-v5) as a managed
AWS SageMaker inference endpoint using parameters from a .env file.
"""

import os
from dotenv import load_dotenv
import sagemaker
from sagemaker.model import Model
import boto3

# print("SAGEMAKER ROLE : ", sagemaker.get_execution_role())

# ---------------------------------------------------------------------
# 1. Load config from .env
# ---------------------------------------------------------------------
load_dotenv()

MODEL_NAME      = os.getenv("MODEL", "nv-embedqa-e5-v5")
IMAGE_TAG       = os.getenv("IMAGE_TAG", "1.10.0")
AWS_REGION      = os.getenv("AWS_REGION", "us-west-2")
ROLE_ARN        = os.getenv("SAGEMAKER_ROLE_ARN")
NGC_API_KEY     = os.getenv("NGC_API_KEY")
INSTANCE_TYPE   = os.getenv("INSTANCE_TYPE", "ml.g5.2xlarge")
INSTANCE_COUNT  = int(os.getenv("INSTANCE_COUNT", "1"))

ENDPOINT_NAME   = f"{MODEL_NAME}-endpoint"
IMAGE_URI       = (
    f"763104351884.dkr.ecr.{AWS_REGION}.amazonaws.com/"
    f"nvidia/nim/{MODEL_NAME}:{IMAGE_TAG}"
)

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
# 3. Create and deploy the SageMaker model
# ---------------------------------------------------------------------

# session = sagemaker.Session(boto_session=boto3.Session(profile_name="personal"))

session = sagemaker.Session(
    boto_session=boto3.Session(profile_name="personal", region_name=AWS_REGION)
)

print(f"📍 SageMaker session region: {session.boto_region_name}")


# model = Model(
#     image_uri=IMAGE_URI,
#     role=ROLE_ARN,
#     name=MODEL_NAME,
#     env={"NGC_API_KEY": NGC_API_KEY},  # passed into container
# )
model = Model(
    image_uri=IMAGE_URI,
    role=ROLE_ARN,
    name=MODEL_NAME,
    env={"NGC_API_KEY": NGC_API_KEY},
    sagemaker_session=session
)


predictor = model.deploy(
    initial_instance_count=INSTANCE_COUNT,
    instance_type=INSTANCE_TYPE,
    endpoint_name=ENDPOINT_NAME,
    wait=True,  # waits until "InService"
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
