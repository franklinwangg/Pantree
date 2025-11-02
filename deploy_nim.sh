#!/usr/bin/env bash
set -e

# -----------------------------
# CONFIGURATION
# -----------------------------
REGION="us-east-1"
REPO_NAME="nim-endpoint"
MODEL_NAME="nim-endpoint-model"
ENDPOINT_CONFIG_NAME="nim-endpoint-config"
ENDPOINT_NAME="nim-endpoint"
INSTANCE_TYPE="ml.m5.large"  # valid SageMaker instance
DOCKER_CONTEXT="./sagemaker_nim_endpoint"
IMAGE="${REPO_NAME}:latest"

# Load secrets from .env if exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$ROLE_ARN" ] || [ -z "$NIM_API_KEY" ]; then
    echo "ERROR: ROLE_ARN and NIM_API_KEY must be set in environment variables or .env"
    exit 1
fi

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
run() { echo "> $1"; eval "$1"; }

get_ecr_uri() {
    ECR_URI=$(aws ecr describe-repositories \
        --repository-names "$REPO_NAME" \
        --query "repositories[0].repositoryUri" \
        --output text --region "$REGION" 2>/dev/null || true)
    if [ -z "$ECR_URI" ]; then
        echo "Creating ECR repository..."
        aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION"
        ECR_URI=$(aws ecr describe-repositories \
            --repository-names "$REPO_NAME" \
            --query "repositories[0].repositoryUri" \
            --output text --region "$REGION")
    fi
    echo "$ECR_URI"
}

build_docker() {
    echo "Building Docker image..."
    DOCKER_BUILDKIT=0 docker build -t "$IMAGE" "$DOCKER_CONTEXT"
}

push_docker() {
    ECR_URI=$(get_ecr_uri)
    echo "ECR URI: $ECR_URI"
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_URI"
    docker tag "$IMAGE" "$ECR_URI:latest"
    docker push "$ECR_URI:latest"
}

deploy_sagemaker() {
    ECR_URI=$(get_ecr_uri)
    echo "Creating SageMaker model..."
    aws sagemaker create-model \
        --model-name "$MODEL_NAME" \
        --primary-container Image="$ECR_URI:latest",Environment="{NIM_API_KEY=$NIM_API_KEY}" \
        --execution-role-arn "$ROLE_ARN" --region "$REGION" || echo "Model may already exist, continuing..."

    echo "Creating endpoint config..."
    aws sagemaker create-endpoint-config \
        --endpoint-config-name "$ENDPOINT_CONFIG_NAME" \
        --production-variants VariantName=AllTraffic,ModelName="$MODEL_NAME",InitialInstanceCount=1,InstanceType="$INSTANCE_TYPE" \
        --region "$REGION" || echo "Endpoint config may already exist, continuing..."

    if aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" >/dev/null 2>&1; then
        echo "Endpoint exists, updating..."
        aws sagemaker update-endpoint --endpoint-name "$ENDPOINT_NAME" --endpoint-config-name "$ENDPOINT_CONFIG_NAME" --region "$REGION"
    else
        echo "Creating endpoint..."
        aws sagemaker create-endpoint --endpoint-name "$ENDPOINT_NAME" --endpoint-config-name "$ENDPOINT_CONFIG_NAME" --region "$REGION"
    fi

    echo "Deployment started. Check AWS Console for endpoint status (InService)."
}

test_endpoint() {
    echo "Testing SageMaker endpoint..."
    python3 - <<EOF
import boto3, json
runtime = boto3.client("sagemaker-runtime", region_name="$REGION")
payload = {"user_id": "u123", "purchases": ["chicken","eggs","chicken","rice","eggs","chicken"]}
resp = runtime.invoke_endpoint(EndpointName="$ENDPOINT_NAME", Body=json.dumps(payload), ContentType="application/json")
print(json.loads(resp["Body"].read()))
EOF
}

# -----------------------------
# PARSE ARGUMENTS
# -----------------------------
ACTION="all"
if [ $# -gt 0 ]; then
    ACTION=$1
fi

case $ACTION in
    build)
        build_docker
        ;;
    push)
        push_docker
        ;;
    deploy)
        deploy_sagemaker
        ;;
    test)
        test_endpoint
        ;;
    all)
        build_docker
        push_docker
        deploy_sagemaker
        test_endpoint
        ;;
    *)
        echo "Usage: $0 [build|push|deploy|test|all]"
        exit 1
        ;;
esac
