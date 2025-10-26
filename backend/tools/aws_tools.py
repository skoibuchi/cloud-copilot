import os
from threading import Lock
from langchain.tools import tool
import boto3
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


# ----------------------------
# AWS Client Manager
# ----------------------------
class AWSClientManager:
    _lock = Lock()
    _ec2_client = None
    _s3_client = None
    _cloudwatch_client = None

    @classmethod
    def get_ec2_client(cls):
        with cls._lock:
            if cls._ec2_client is None:
                region = os.getenv("AWS_REGION", "us-east-1")
                cls._ec2_client = boto3.client("ec2", region_name=region)
            return cls._ec2_client

    @classmethod
    def get_s3_client(cls):
        with cls._lock:
            if cls._s3_client is None:
                region = os.getenv("AWS_REGION", "us-east-1")
                cls._s3_client = boto3.client("s3", region_name=region)
            return cls._s3_client

    @classmethod
    def get_cloudwatch_client(cls):
        with cls._lock:
            if cls._cloudwatch_client is None:
                region = os.getenv("AWS_REGION", "us-east-1")
                cls._cloudwatch_client = boto3.client("cloudwatch", region_name=region)
            return cls._cloudwatch_client


# ----------------------------
# VM Operations
# ----------------------------
@tool
def list_vms(_: str) -> list[str]:
    """
    Return a list of running EC2 instances.
    稼働中のEC2インスタンスをリストで返す
    """
    client = AWSClientManager.get_ec2_client()
    response = client.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
    instances = [
        next((tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"), instance["InstanceId"])
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]
    return instances or []


@tool
def start_vm(instance_id: str) -> str:
    """
    Start the specified EC2 instance.
    指定したEC2インスタンスを起動する
    """
    client = AWSClientManager.get_ec2_client()
    client.start_instances(InstanceIds=[instance_id])
    return f"EC2 instance {instance_id} started."


@tool
def stop_vm(instance_id: str) -> str:
    """
    Stop the specified EC2 instance.
    指定したEC2インスタンスを停止する
    """
    client = AWSClientManager.get_ec2_client()
    client.stop_instances(InstanceIds=[instance_id])
    return f"EC2 instance {instance_id} stopped."


# ----------------------------
# Storage Operations
# ----------------------------
@tool
def list_buckets(_: str) -> list[str]:
    """
    Return a list of S3 buckets.
    S3バケットの一覧をリストで返す
    """
    client = AWSClientManager.get_s3_client()
    response = client.list_buckets()
    buckets = [b["Name"] for b in response.get("Buckets", [])]
    return buckets or []


@tool
def create_bucket(bucket_name: str) -> str:
    """
    Create a new S3 bucket.
    新しいS3バケットを作成する
    """
    region = os.getenv("AWS_REGION", "us-east-1")
    client = AWSClientManager.get_s3_client()
    client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region})
    return f"S3 bucket {bucket_name} created."


class UploadFileInput(BaseModel):
    file_path: str = Field(..., description="Local path to the file to upload")
    bucket_name: str = Field(..., description="Target S3 bucket name")
    object_name: Optional[str] = Field(None, description="Object name in S3, defaults to file name")


@tool(args_schema=UploadFileInput)
def upload_file_to_bucket(file_path: str, bucket_name: str, object_name: Optional[str] = None) -> dict:
    """
    Upload a file to the specified S3 bucket.
    指定したS3バケットにファイルをアップロードする
    """
    import os
    client = AWSClientManager.get_s3_client()
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        client.upload_file(file_path, bucket_name, object_name)
        return f"File '{object_name}' uploaded to bucket '{bucket_name}'."
    except Exception:
        return f"File '{object_name}' upload failed."


# ----------------------------
# Monitoring Operations
# ----------------------------
class VMUsageInput(BaseModel):
    instance_id: str = Field(..., description="EC2 instance ID")
    n: int = Field(..., description="Past minutes to calculate average")


@tool(args_schema=VMUsageInput)
def list_vm_cpu_usage(instance_id: str, n: int) -> str:
    """
    Return the average CPU usage of the specified EC2 instance over the past n minutes.
    指定EC2の過去n分のCPU使用率平均を返す
    """
    client = AWSClientManager.get_cloudwatch_client()
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=n)

    metrics = client.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=["Average"]
    )

    data_points = [dp["Average"] for dp in metrics.get("Datapoints", [])]
    if not data_points:
        return f"No CPU usage data found for EC2 instance {instance_id}."
    avg = sum(data_points) / len(data_points)
    return f"Average CPU usage for EC2 instance {instance_id}: {avg:.2f}%"


# ----------------------------
# Tool Registration
# ----------------------------
aws_tools = [
    list_vms,
    start_vm,
    stop_vm,
    list_buckets,
    create_bucket,
    upload_file_to_bucket,
    list_vm_cpu_usage,
]
