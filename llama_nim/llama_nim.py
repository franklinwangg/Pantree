import boto3
import time
import json

# ---------- CONFIGURATION ----------
REGION = "us-west-2"
IMAGE_URI = "729386419841.dkr.ecr.us-west-2.amazonaws.com/nv-llama3-8b-instruct:1.0.0"  # Replace if needed
ROLE_ARN = "arn:aws:iam::<YOUR-ACCOUNT-ID>:role/<SAGEMAKER-EXECUTION-ROLE>"             # Replace with your IAM role
MODEL_NAME = "llama-nim-model"
ENDPOINT_CONFIG_NAME = "llama-nim-endpoint-config"
ENDPOINT_NAME = "llama-nim-endpoint"
INSTANCE_TYPE = "ml.g5.2xlarge"  # Adjust if using different GPU
# ----------------------------------

sagemaker = boto3.client("sagemaker", region_name=REGION)


def create_model():
    print(f"🧠 Creating SageMaker model: {MODEL_NAME} ...")
    try:
        sagemaker.create_model(
            ModelName=MODEL_NAME,
            PrimaryContainer={
                "Image": IMAGE_URI,
                "Mode": "SingleModel",
                "Environment": {}
            },
            ExecutionRoleArn=ROLE_ARN
        )
    except sagemaker.exceptions.ClientError as e:
        if "already exists" in str(e):
            print("✅ Model already exists, skipping creation.")
        else:
            raise e


def create_endpoint_config():
    print(f"⚙️ Creating endpoint config: {ENDPOINT_CONFIG_NAME} ...")
    try:
        sagemaker.create_endpoint_config(
            EndpointConfigName=ENDPOINT_CONFIG_NAME,
            ProductionVariants=[
                {
                    "VariantName": "AllTraffic",
                    "ModelName": MODEL_NAME,
                    "InstanceType": INSTANCE_TYPE,
                    "InitialInstanceCount": 1,
                }
            ]
        )
    except sagemaker.exceptions.ClientError as e:
        if "already exists" in str(e):
            print("✅ Endpoint config already exists, skipping creation.")
        else:
            raise e


def create_endpoint():
    print(f"🚀 Deploying endpoint: {ENDPOINT_NAME} ...")
    try:
        sagemaker.create_endpoint(
            EndpointName=ENDPOINT_NAME,
            EndpointConfigName=ENDPOINT_CONFIG_NAME
        )
    except sagemaker.exceptions.ClientError as e:
        if "already exists" in str(e):
            print("✅ Endpoint already exists, skipping creation.")
        else:
            raise e

    wait_for_endpoint(ENDPOINT_NAME)


def wait_for_endpoint(endpoint_name):
    print("⏳ Waiting for endpoint to reach 'InService' status...")
    sm_runtime = boto3.client("sagemaker", region_name=REGION)
    while True:
        response = sm_runtime.describe_endpoint(EndpointName=endpoint_name)
        status = response["EndpointStatus"]
        print(f"   Status: {status}")
        if status in ["InService", "Failed"]:
            break
        time.sleep(60)

    if status == "InService":
        print(f"✅ Endpoint is live! Name: {endpoint_name}")
    else:
        print(f"❌ Deployment failed. Check CloudWatch logs for details.")


def test_inference():
    print("🧪 Testing inference...")
    runtime = boto3.client("sagemaker-runtime", region_name=REGION)
    prompt = {"input": "Explain the difference between cloud and edge computing."}

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(prompt)
    )
    print("Model response:\n", response["Body"].read().decode("utf-8"))


if __name__ == "__main__":
    create_model()
    create_endpoint_config()
    create_endpoint()
    test_inference()
