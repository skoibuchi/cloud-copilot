import os
from langchain.tools import tool
from pydantic import BaseModel, Field
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient
from azure.mgmt.monitor import MonitorManagementClient
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.database.database import SessionLocal
from app.services.cloud_config_service import get_configs_dict


# ----------------------------
# Input Schemas for Tools
# ----------------------------
class FileOperationInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    container_name: str = Field(..., description="Target container name")
    account_name: str = Field(..., description="Azure account name")


class UploadFileInput(FileOperationInput):
    file_path: str = Field(..., description="Local path to the file to upload")
    blob_name: Optional[str] = Field(None, description="Blob name in container, defaults to file name")


class DeleteFileInput(FileOperationInput):
    blob_name: str = Field(..., description="Blob name in container")


class VMUsageInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    vm_name: str = Field(..., description="VM instance name")
    n: int = Field(..., description="Past minutes to calculate average")
    account_name: str = Field(..., description="Azure account name")


# ----------------------------
# Helper: Create user-specific Azure clients
# ----------------------------
def get_azure_clients(user_id: int, account_name: Optional[str] = None):
    """
    Create Azure clients using user's credentials from runtime context.
    ユーザーごとの認証情報を runtime.context.credentials からロードしてクライアントを作成
    """
    db = SessionLocal()
    credentials = get_configs_dict(db=db, user_id=user_id)
    db.close()
    azure_accounts = credentials.get("aws", [])
    if account_name:
        creds = next((a for a in azure_accounts if a["name"] == account_name), None)
        if not creds:
            raise ValueError(f"Azure account '{account_name}' not found.")
    else:
        creds = azure_accounts[0]

    tenant_id = creds["tenant_id"]
    client_id = creds["client_id"]
    client_secret = creds["client_secret"]
    subscription_id = creds["subscription_id"]
    resource_group = creds["resource_group"]

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    compute_client = ComputeManagementClient(credential, subscription_id)
    storage_client = StorageManagementClient(credential, subscription_id)
    monitor_client = MonitorManagementClient(credential, subscription_id)

    # Blob clientsキャッシュ用辞書
    blob_clients = {}

    return compute_client, storage_client, monitor_client, blob_clients, subscription_id, resource_group


def get_blob_service_client(storage_client: StorageManagementClient, blob_clients: dict, account_name: str, resource_group: str) -> BlobServiceClient:
    """
    Get or create BlobServiceClient for a given storage account.
    指定ストレージアカウント用のBlobServiceClientを取得または作成
    """
    if account_name not in blob_clients:
        keys = storage_client.storage_accounts.list_keys(resource_group, account_name)
        account_key = keys.keys[0].value
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        blob_clients[account_name] = BlobServiceClient.from_connection_string(conn_str)
    return blob_clients[account_name]


# ----------------------------
# VM Operations
# ----------------------------
async def _list_vms(user_id: int, account_name: Optional[str] = None) -> list[str]:
    """
    List running VM instances for this user.
    このユーザーの稼働中VMインスタンスをリストで返す
    """
    compute_client, _, _, _, _, resource_group = get_azure_clients(user_id, account_name)
    vms = compute_client.virtual_machines.list(resource_group_name=resource_group)
    return [vm.name for vm in vms] or []


async def _start_vm(user_id: int, vm_name: str, account_name: Optional[str] = None) -> str:
    """
    Start the specified VM instance for this user.
    このユーザーの指定VMを起動する
    """
    compute_client, _, _, _, _, resource_group = get_azure_clients(user_id, account_name)
    compute_client.virtual_machines.begin_start(resource_group, vm_name).result()
    return f"VM {vm_name} started."


async def _stop_vm(user_id: int, vm_name: str, account_name: Optional[str] = None) -> str:
    """
    Stop the specified VM instance for this user.
    このユーザーの指定VMを停止する
    """
    compute_client, _, _, _, _, resource_group = get_azure_clients(user_id, account_name)
    compute_client.virtual_machines.begin_deallocate(resource_group, vm_name).result()
    return f"VM {vm_name} stopped."


# ----------------------------
# Storage Operations
# ----------------------------
async def _list_buckets(user_id: int, account_name: str) -> list[str]:
    """
    List containers in the given Storage Account for this user.
    このユーザーの指定ストレージアカウント内のコンテナ一覧を返す
    """
    _, storage_client, _, blob_clients, _, resource_group = get_azure_clients(user_id, account_name)
    blob_service = get_blob_service_client(storage_client, blob_clients, account_name, resource_group)
    containers = [c.name for c in blob_service.list_containers()]
    return containers


async def _create_bucket(user_id: int, account_name: str, container_name: str) -> str:
    """
    Create a new container in the given Storage Account for this user.
    このユーザー用の指定ストレージアカウントに新しいコンテナを作成
    """
    _, storage_client, _, blob_clients, _, resource_group = get_azure_clients(user_id, account_name)
    blob_service = get_blob_service_client(storage_client, blob_clients, account_name, resource_group)
    blob_service.create_container(container_name)
    return f"Container '{container_name}' created in Storage Account '{account_name}'."


async def _upload_file_to_bucket(user_id: int, file_path: str, container_name: str, blob_name: Optional[str], account_name: str) -> str:
    """
    Upload a file to the specified Azure container for this user.
    このユーザー用の指定Azureコンテナにファイルをアップロード
    """
    _, storage_client, _, blob_clients, _, resource_group = get_azure_clients(user_id, account_name)
    blob_service = get_blob_service_client(storage_client, blob_clients, account_name, resource_group)
    container_client = blob_service.get_container_client(container_name)
    if not blob_name:
        blob_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        container_client.upload_blob(name=blob_name, data=f, overwrite=True)
    return f"File '{blob_name}' uploaded to container '{container_name}' in Storage Account '{account_name}'."


async def _list_files(user_id: int, container_name: str, account_name: str) -> list[str]:
    """
    List all blobs in the specified container for this user.
    指定コンテナ内のBlob一覧を返す
    """
    _, storage_client, _, blob_clients, _, resource_group = get_azure_clients(user_id, account_name)
    blob_service = get_blob_service_client(storage_client, blob_clients, account_name, resource_group)
    container_client = blob_service.get_container_client(container_name)
    return [blob.name for blob in container_client.list_blobs()]


async def _delete_file(user_id: int, container_name: str, blob_name: str, account_name: str) -> str:
    """
    Delete a blob from the specified container for this user.
    指定コンテナからBlobを削除
    """
    _, storage_client, _, blob_clients, _, resource_group = get_azure_clients(user_id, account_name)
    blob_service = get_blob_service_client(storage_client, blob_clients, account_name, resource_group)
    container_client = blob_service.get_container_client(container_name)
    container_client.delete_blob(blob_name)
    return f"Blob '{blob_name}' deleted from container '{container_name}' in Storage Account '{account_name}'."


# ----------------------------
# Monitoring Operations
# ----------------------------
async def _list_vm_cpu_usage(user_id: int, vm_name: str, n: int, account_name: Optional[str] = None) -> str:
    """
    Return average CPU usage for the specified VM in the past n minutes for this user.
    このユーザーの指定VMの過去n分間CPU使用率平均を返す
    """
    _, _, monitor_client, _, _, resource_group = get_azure_clients(user_id, account_name)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=n)

    subscription_id = ""
    creds = get_configs_dict(user_id)
    for cred in creds.get("azure", []):
        if cred["name"] == account_name:
            subscription_id = cred["subscription_id"]

    metrics_data = monitor_client.metrics.list(
        resource_id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
        timespan=f"{start_time}/{end_time}",
        interval="PT1M",
        metricnames="Percentage CPU",
        aggregation="Average"
    )

    usage_list = []
    for item in metrics_data.value:
        for timeserie in item.timeseries:
            for data in timeserie.data:
                if data.average is not None:
                    usage_list.append(data.average)

    if not usage_list:
        return f"No CPU usage data found for {vm_name}."
    avg = sum(usage_list) / len(usage_list)
    return f"Average CPU usage for {vm_name}: {avg:.2f}%"


# ----------------------------
# Tool Registration
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


def create_azure_tools() -> list:
    """
    Return a list of Azure tools for the agent.
    エージェント用のAzureツールリストを返す
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
        list_vm_cpu_usage,
    ]
