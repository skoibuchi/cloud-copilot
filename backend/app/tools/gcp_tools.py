import os
from langchain.tools import tool
from google.oauth2 import service_account
from google.cloud import compute_v1, storage, monitoring_v3
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.database.database import SessionLocal
from app.services.cloud_config_service import get_configs_dict


# ----------------------------
# Input Schemas for Tools
# ----------------------------
class UploadFileInput(BaseModel):
    user_id: int = Field(..., description="ユーザーID")
    file_path: str = Field(..., description="Local path to the file to upload")
    bucket_name: str = Field(..., description="Target GCS bucket name")
    blob_name: Optional[str] = Field(None, description="Blob name in bucket, defaults to file name")
    account_name: str = Field(..., description="GCP account name")


class VMUsageInput(BaseModel):
    user_id: int = Field(..., description="ユーザーID")
    instance_name: str = Field(..., description="VM instance name")
    n: int = Field(..., description="Past minutes to calculate average")
    account_name: str = Field(..., description="GCP account name")


# ----------------------------
# Helper: Create user-specific GCP clients
# ----------------------------
def get_gcp_clients(user_id: int, account_name: Optional[str] = None):
    """
    Create GCP clients using user's credentials from runtime context.
    ユーザーごとの認証情報を runtime.context.credentials からロードしてクライアントを作成
    """
    db = SessionLocal()
    credentials = get_configs_dict(db=db, user_id=user_id)
    db.close()
    gcp_accounts = credentials.get("gcp", [])
    creds_dict = next((a for a in gcp_accounts if a["name"] == account_name), None)
    if not creds_dict:
        raise ValueError(f"GCP account '{account_name}' not found for user.")

    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    project_id = creds_dict.get("project_id")
    zone = creds_dict.get("zone", "us-central1-a")

    compute_client = compute_v1.InstancesClient(credentials=credentials)
    storage_client = storage.Client(project=project_id, credentials=credentials)
    monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)

    return compute_client, storage_client, monitoring_client, project_id, zone


# ----------------------------
# VM Operations
# ----------------------------
async def _list_vms(user_id: int, account_name: Optional[str] = None) -> list[str]:
    """
    List running VM instances for this user.
    このユーザーの稼働中VMインスタンスをリストで返す
    """
    compute_client, _, _, project_id, zone = get_gcp_clients(user_id, account_name)
    vms = compute_client.list(project=project_id, zone=zone)
    return [vm.name for vm in vms] or []


async def _start_vm(user_id: int, instance_name: str, account_name: Optional[str] = None) -> str:
    """
    Start the specified VM instance for this user.
    このユーザーの指定VMを起動する
    """
    compute_client, _, _, project_id, zone = get_gcp_clients(user_id, account_name)
    operation = compute_client.start(project=project_id, zone=zone, instance=instance_name)
    return f"VM {instance_name} started (operation: {operation.name})."


async def _stop_vm(user_id: int, instance_name: str, account_name: Optional[str] = None) -> str:
    """
    Stop the specified VM instance for this user.
    このユーザーの指定VMを停止する
    """
    compute_client, _, _, project_id, zone = get_gcp_clients(user_id, account_name)
    operation = compute_client.stop(project=project_id, zone=zone, instance=instance_name)
    return f"VM {instance_name} stopped (operation: {operation.name})."


# ----------------------------
# Storage Operations
# ----------------------------
async def _list_buckets(user_id: int, account_name: Optional[str] = None) -> list[str]:
    """
    List all storage buckets for this user.
    このユーザーのStorageバケット一覧を返す
    """
    _, storage_client, _, _, _ = get_gcp_clients(user_id, account_name)
    buckets = storage_client.list_buckets()
    return [b.name for b in buckets] or []


async def _create_bucket(user_id: int, bucket_name: str, account_name: Optional[str] = None) -> str:
    """
    Create a new storage bucket for this user.
    このユーザー用の新しいStorageバケットを作成
    """
    _, storage_client, _, project_id, _ = get_gcp_clients(user_id, account_name)
    bucket = storage_client.create_bucket(bucket_name, project=project_id)
    return f"Bucket {bucket.name} created."


async def _upload_file_to_bucket(user_id: int, file_path: str, bucket_name: str, blob_name: Optional[str], account_name: Optional[str] = None) -> str:
    """
    Upload a local file to the specified GCS bucket for this user.
    このユーザー用の指定Google Cloud Storageバケットにファイルをアップロード
    """
    _, storage_client, _, _, _ = get_gcp_clients(user_id, account_name)
    if not blob_name:
        blob_name = os.path.basename(file_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    return f"File '{blob_name}' uploaded to bucket '{bucket_name}'."


# ----------------------------
# Monitoring Operations
# ----------------------------
async def _list_vm_cpu_usage(user_id: int, instance_name: str, n: int, account_name: Optional[str] = None) -> str:
    """
    Return average CPU usage for the specified VM over past n minutes for this user.
    このユーザーの指定VMの過去n分間CPU使用率平均を返す
    """
    _, _, monitoring_client, project_id, _ = get_gcp_clients(user_id, account_name)
    project_name = f"projects/{project_id}"

    now = datetime.now(timezone.utc)
    interval = monitoring_v3.TimeInterval()
    interval.start_time.FromDatetime(now - timedelta(minutes=n))
    interval.end_time.FromDatetime(now)

    results = monitoring_client.list_time_series(
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
list_vms = tool(_list_vms)
start_vm = tool(_start_vm)
stop_vm = tool(_stop_vm)
create_bucket = tool(_create_bucket)
list_buckets = tool(_list_buckets)
upload_file_to_bucket = tool(_upload_file_to_bucket, args_schema=UploadFileInput)
list_vm_cpu_usage = tool(_list_vm_cpu_usage, args_schema=VMUsageInput)


def create_gcp_tools() -> list:
    """
    Return a list of GCP tools for the agent.
    エージェント用のGCPツールリストを返す
    """
    return [
        list_vms,
        start_vm,
        stop_vm,
        list_buckets,
        create_bucket,
        upload_file_to_bucket,
        list_vm_cpu_usage,
    ]
