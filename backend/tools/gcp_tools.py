import os
from threading import Lock
from langchain.tools import tool
from google.cloud import compute_v1, storage, monitoring_v3
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


# ----------------------------
# GCP Client Manager
# ----------------------------
class GCPClientManager:
    _lock = Lock()
    _compute_client = None
    _storage_client = None
    _monitoring_client = None

    @classmethod
    def get_compute_client(cls):
        with cls._lock:
            if cls._compute_client is None:
                cls._compute_client = compute_v1.InstancesClient()
            return cls._compute_client

    @classmethod
    def get_storage_client(cls):
        with cls._lock:
            if cls._storage_client is None:
                project_id = os.getenv("GCP_PROJECT_ID")
                cls._storage_client = storage.Client(project=project_id)
            return cls._storage_client

    @classmethod
    def get_monitoring_client(cls):
        with cls._lock:
            if cls._monitoring_client is None:
                cls._monitoring_client = monitoring_v3.MetricServiceClient()
            return cls._monitoring_client


# ----------------------------
# VM Operations
# ----------------------------
@tool
def list_vms(_: str) -> list[str]:
    """
    Return a list of running VM instances.
    稼働中のVMインスタンスを返す
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    zone = os.getenv("GCP_ZONE", "us-central1-a")
    client = GCPClientManager.get_compute_client()
    vms = client.list(project=project_id, zone=zone)
    return [vm.name for vm in vms] or []


@tool
def start_vm(instance_name: str) -> str:
    """
    Start the specified VM instance.
    指定したVMを起動する
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    zone = os.getenv("GCP_ZONE", "us-central1-a")
    client = GCPClientManager.get_compute_client()
    operation = client.start(project=project_id, zone=zone, instance=instance_name)
    return f"VM {instance_name} started (operation: {operation.name})."


@tool
def stop_vm(instance_name: str) -> str:
    """
    Stop the specified VM instance.
    指定したVMを停止する
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    zone = os.getenv("GCP_ZONE", "us-central1-a")
    client = GCPClientManager.get_compute_client()
    operation = client.stop(project=project_id, zone=zone, instance=instance_name)
    return f"VM {instance_name} stopped (operation: {operation.name})."


# ----------------------------
# Storage Operations
# ----------------------------
@tool
def list_buckets(_: str) -> list[str]:
    """
    List all storage buckets.
    Storageバケットの一覧を返す
    """
    client = GCPClientManager.get_storage_client()
    buckets = client.list_buckets()
    return [b.name for b in buckets] or []


@tool
def create_bucket(bucket_name: str) -> str:
    """
    Create a new storage bucket.
    新しいStorageバケットを作成する
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    client = GCPClientManager.get_storage_client()
    bucket = client.create_bucket(bucket_name, project=project_id)
    return f"Bucket {bucket.name} created."


class UploadFileInput(BaseModel):
    file_path: str = Field(..., description="Local path to the file to upload")
    bucket_name: str = Field(..., description="Target GCS bucket name")
    blob_name: Optional[str] = Field(None, description="blob name in bucket, defaults to file name")


@tool(args_schema=UploadFileInput)
def upload_file_to_bucket(file_path: str, bucket_name: str, blob_name: str) -> str:
    """
    Upload a local file to the specified Google Cloud Storage bucket.
    指定したGoogle Cloud Storageバケットにファイルをアップロードする
    """
    client = GCPClientManager.get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    return f"File '{blob_name}' uploaded to bucket '{bucket_name}'."


# ----------------------------
# Monitoring Operations
# ----------------------------
class VMUsageInput(BaseModel):
    instance_name: str = Field(..., description="VM instance name")
    n: int = Field(..., description="Past minutes to calculate average")


@tool(args_schema=VMUsageInput)
def list_vm_cpu_usage(instance_name: str, n: int) -> str:
    """
    Return average CPU usage for the specified VM in the past n minutes.
    指定VMの過去n分のCPU使用率平均を返す
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    client = GCPClientManager.get_monitoring_client()
    project_name = f"projects/{project_id}"

    now = datetime.now(timezone.utc)
    interval = monitoring_v3.TimeInterval()
    interval.start_time.FromDatetime(now - timedelta(minutes=n))
    interval.end_time.FromDatetime(now)

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": 'metric.type="compute.googleapis.com/instance/cpu/utilization"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
        }
    )

    usage_list = [point.value.double_value for ts in results for point in ts.points]
    if not usage_list:
        return f"No CPU usage data found for {instance_name}."
    avg = sum(usage_list) / len(usage_list)
    return f"Average CPU usage for {instance_name}: {avg*100:.2f}%"


# ----------------------------
# Tool Registration
# ----------------------------
gcp_tools = [
    list_vms,
    start_vm,
    stop_vm,
    list_buckets,
    create_bucket,
    upload_file_to_bucket,
    list_vm_cpu_usage,
]
