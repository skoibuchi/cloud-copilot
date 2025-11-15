from langchain.tools import tool
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional
import boto3
import os
from app.database.database import SessionLocal
from app.services.cloud_config_service import get_configs_dict


# ----------------------------
# Input Schemas for Tools
# ----------------------------
class FileOperationInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    bucket_name: str = Field(..., description="Target S3 bucket")
    account_name: Optional[str] = Field(..., description="AWS account name")


class UploadFileInput(FileOperationInput):
    file_path: str = Field(..., description="Local path to file")
    object_name: Optional[str] = Field(None, description="S3 object name, defaults to file name")


class DeleteFileInput(FileOperationInput):
    object_name: str = Field(..., description="S3 object name")


class VMUsageInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    instance_id: str = Field(..., description="EC2 instance ID")
    n: int = Field(..., description="Past minutes to calculate average")
    account_name: str = Field(..., description="AWS account name")


# ----------------------------
# Helper: Create user-specific boto3 clients
# ----------------------------
def get_client(service: str, user_id: int, account_name: Optional[str] = None):
    """
    Create boto3 client using user's credentials from context.
    ユーザーごとの認証情報を runtime.context.credentials からロードしてクライアントを作成
    """
    db = SessionLocal()
    credentials = get_configs_dict(db=db, user_id=user_id)
    db.close()
    aws_accounts = credentials.get("aws", [])
    if not aws_accounts:
        raise ValueError("No AWS credentials found for user.")

    # アカウント名で選択、なければ最初のアカウント
    if account_name:
        creds = next((a for a in aws_accounts if a["name"] == account_name), None)
        if not creds:
            raise ValueError(f"AWS account '{account_name}' not found.")
    else:
        creds = aws_accounts[0]

    return boto3.client(
        service,
        region_name=creds["region"],
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token")
    )


# ----------------------------
# EC2 VM Operations / EC2操作
# ----------------------------
async def _list_vms(user_id: str, account_name: Optional[str] = None) -> list[str]:
    """
    Return a list of running EC2 instances.
    稼働中のEC2インスタンスのリストを返す
    """
    client = get_client("ec2", user_id, account_name)
    response = client.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
    instances = [
        next((tag["Value"] for tag in i.get("Tags", []) if tag["Key"] == "Name"), i["InstanceId"])
        for r in response["Reservations"] for i in r["Instances"]
    ]
    return instances or []


async def _start_vm(user_id: int, instance_id: str, account_name: Optional[str] = None) -> str:
    """
    Start the specified EC2 instance.
    指定したEC2インスタンスを起動する
    """
    client = get_client("ec2", user_id, account_name)
    client.start_instances(InstanceIds=[instance_id])
    return f"EC2 instance {instance_id} started."


async def _stop_vm(user_id: int, instance_id: str, account_name: Optional[str] = None) -> str:
    """
    Stop the specified EC2 instance.
    指定したEC2インスタンスを停止する
    """
    client = get_client("ec2", user_id, account_name)
    client.stop_instances(InstanceIds=[instance_id])
    return f"EC2 instance {instance_id} stopped."


# ----------------------------
# S3 Storage Operations / S3操作
# ----------------------------
async def _list_buckets(user_id: int, account_name: Optional[str] = None) -> list[str]:
    """
    Return a list of S3 buckets.
    S3バケットの一覧を返す
    """
    client = get_client("s3", user_id, account_name)
    response = client.list_buckets()
    return [b["Name"] for b in response.get("Buckets", [])]


async def _create_bucket(user_id: int, bucket_name: str, region: str, account_name: Optional[str] = None) -> str:
    """
    Create a new S3 bucket.
    新しいS3バケットを作成する
    """
    client = get_client("s3", user_id, account_name)
    client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region}
    )
    return f"S3 bucket {bucket_name} created."


async def _upload_file_to_bucket(user_id: int, file_path: str, bucket_name: str, object_name: Optional[str], account_name: Optional[str] = None) -> str:
    """
    Upload a file to the specified S3 bucket.
    指定したS3バケットにファイルをアップロードする
    """
    client = get_client("s3", user_id, account_name)
    if object_name is None:
        object_name = os.path.basename(file_path)
    client.upload_file(file_path, bucket_name, object_name)
    return f"File '{object_name}' uploaded to bucket '{bucket_name}'."


async def _list_files(user_id: int, bucket_name: str, account_name: Optional[str] = None) -> list[str]:
    """
    List all objects in the specified S3 bucket.
    指定したS3バケット内のオブジェクト一覧を返す
    """
    client = get_client("s3", user_id, account_name)
    response = client.list_objects_v2(Bucket=bucket_name)
    contents = response.get("Contents", [])
    return [obj["Key"] for obj in contents] if contents else []


async def _delete_file(user_id: int, bucket_name: str, object_name: str, account_name: Optional[str] = None) -> str:
    """
    Delete an object from the specified S3 bucket.
    指定したS3バケットからオブジェクトを削除する
    """
    client = get_client("s3", user_id, account_name)
    client.delete_object(Bucket=bucket_name, Key=object_name)
    return f"File '{object_name}' deleted from bucket '{bucket_name}'."


# ----------------------------
# CloudWatch Monitoring / CloudWatch監視
# ----------------------------
def _list_vm_cpu_usage(user_id: int, instance_id: str, n: int, account_name: Optional[str] = None) -> str:
    """
    Return average CPU usage of the specified EC2 instance over past n minutes.
    指定EC2インスタンスの過去n分のCPU使用率平均を返す
    """
    client = get_client("cloudwatch", user_id, account_name)
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
# Tool Registration / ツール登録
# ----------------------------
list_vms = tool(_list_vms)
start_vm = tool(_start_vm)
stop_vm = tool(_stop_vm)
create_bucket = tool(_create_bucket)
list_buckets = tool(_list_buckets)
upload_file_to_bucket = tool(_upload_file_to_bucket, args_schema=UploadFileInput)
list_files = tool(_list_files, args_schema=FileOperationInput)
delete_file = tool(_delete_file, args_schema=FileOperationInput)
list_vm_cpu_usage = tool(_list_vm_cpu_usage, args_schema=VMUsageInput)


def create_aws_tools() -> list:
    """
    Return a list of AWS tools for the agent.
    エージェント用のAWSツールリストを返す
    """
    return [
        list_vms,
        start_vm,
        stop_vm,
        list_buckets,
        create_bucket,
        upload_file_to_bucket,
        list_files,
        delete_file,
        list_vm_cpu_usage
    ]
