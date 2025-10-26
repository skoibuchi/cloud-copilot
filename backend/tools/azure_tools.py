import os
from threading import Lock
from langchain.tools import tool
from pydantic import BaseModel, Field
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient
from azure.mgmt.monitor import MonitorManagementClient
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


# ----------------------------
# Azure Client Manager
# ----------------------------
class AzureClientManager:
    _lock = Lock()
    _compute_client = None
    _storage_client = None
    _monitor_client = None
    _blob_clients = {}
    _credential = None

    @classmethod
    def get_credential(cls):
        with cls._lock:
            if cls._credential is None:
                cls._credential = DefaultAzureCredential()
            return cls._credential

    @classmethod
    def get_compute_client(cls):
        with cls._lock:
            if cls._compute_client is None:
                credential = cls.get_credential()
                subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
                cls._compute_client = ComputeManagementClient(credential, subscription_id)
            return cls._compute_client

    @classmethod
    def get_storage_client(cls):
        with cls._lock:
            if cls._storage_client is None:
                credential = cls.get_credential()
                subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
                cls._storage_client = StorageManagementClient(credential, subscription_id)
            return cls._storage_client

    @classmethod
    def get_monitor_client(cls):
        with cls._lock:
            if cls._monitor_client is None:
                credential = cls.get_credential()
                subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
                cls._monitor_client = MonitorManagementClient(credential, subscription_id)
            return cls._monitor_client

    @classmethod
    def get_storage_account_key(cls, account_name: str) -> str:
        resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        client = cls.get_storage_client()
        keys = client.storage_accounts.list_keys(resource_group, account_name)
        return keys.keys[0].value

    @classmethod
    def get_blob_service_client(cls, account_name: str) -> BlobServiceClient:
        with cls._lock:
            if account_name not in cls._blob_clients:
                account_key = cls.get_storage_account_key(account_name)
                conn_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
                cls._blob_clients[account_name] = BlobServiceClient.from_connection_string(conn_str)
            return cls._blob_clients[account_name]


# ----------------------------
# VM Operations
# ----------------------------
@tool
def list_vms(_: str) -> list[str]:
    """
    Return a list of running VM instances.
    稼働中のVMインスタンスを返す
    """
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    client = AzureClientManager.get_compute_client()
    vms = client.virtual_machines.list(resource_group_name=resource_group)
    return [vm.name for vm in vms] or []


@tool
def start_vm(vm_name: str) -> str:
    """
    Start the specified VM instance.
    指定したVMを起動する
    """
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    client = AzureClientManager.get_compute_client()
    client.virtual_machines.begin_start(resource_group, vm_name).result()
    return f"VM {vm_name} started."


@tool
def stop_vm(vm_name: str) -> str:
    """
    Stop the specified VM instance.
    指定したVMを停止する
    """
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    client = AzureClientManager.get_compute_client()
    client.virtual_machines.begin_deallocate(resource_group, vm_name).result()
    return f"VM {vm_name} stopped."


# ----------------------------
# Storage Operations
# ----------------------------
@tool
def list_buckets(account_name: str) -> list[str]:
    """
    List containers in the given Storage Account.
    コンテナの一覧を返す
    """
    blob_service = AzureClientManager.get_blob_service_client(account_name)
    containers = [c.name for c in blob_service.list_containers()]
    return containers


@tool
def create_bucket(account_name: str, container_name: str) -> str:
    """
    Create a new container in the given Storage Account.
    新しいコンテナを作成する
    """
    blob_service = AzureClientManager.get_blob_service_client(account_name)
    blob_service.create_container(container_name)
    return f"Container '{container_name}' created in Storage Account '{account_name}'."


class UploadFileInput(BaseModel):
    file_path: str = Field(..., description="Local path to the file to upload")
    account_name: str = Field(..., description="Azure account name")
    container_name: str = Field(..., description="Target container name")
    blob_name: Optional[str] = Field(None, description="blob name in container, defaults to file name")


@tool(args_schema=UploadFileInput)
def upload_file_to_bucket(file_path: str, account_name: str, container_name: str, blob_name: str) -> str:
    """
    Upload a file to the specified Azure container.
    指定したAzureのコンテナにファイルをアップロードする
    """
    blob_service = AzureClientManager.get_blob_service_client(account_name)
    container_client = blob_service.get_container_client(container_name)
    with open(file_path, "rb") as f:
        container_client.upload_blob(name=blob_name, data=f, overwrite=True)
    return f"File '{blob_name}' uploaded to container '{container_name}' in Storage Account '{account_name}'."


# ----------------------------
# Monitoring Operations
# ----------------------------
class VMUsageInput(BaseModel):
    vm_name: str = Field(..., description="VM instance name")
    n: int = Field(..., description="Past minutes to calculate average")


@tool(args_schema=VMUsageInput)
def list_vm_cpu_usage(vm_name: str, n: int) -> str:
    """
    Return average CPU usage for the specified VM in the past n minutes.
    指定VMの過去n分のCPU使用率平均を返す
    """
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    client = AzureClientManager.get_monitor_client()
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=n)

    metrics_data = client.metrics.list(
        resource_id=f"/subscriptions/{os.getenv('AZURE_SUBSCRIPTION_ID')}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
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
azure_tools = [
    list_vms,
    start_vm,
    stop_vm,
    list_buckets,
    create_bucket,
    upload_file_to_bucket,
    list_vm_cpu_usage,
]
