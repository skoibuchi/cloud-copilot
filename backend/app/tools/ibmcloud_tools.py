from langchain.tools import tool
from pydantic import BaseModel, Field
from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
import ibm_boto3
from ibm_botocore.client import Config
from typing import Optional
from app.database.database import SessionLocal
from app.services.cloud_config_service import get_configs_dict


# ----------------------------
# Input Schemas for Tools
# ----------------------------
class FileOperationInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    bucket_name: str = Field(..., description="Target ICOS bucket name")
    account_name: str = Field(..., description="IBM Cloud account name to use")


class UploadFileInput(FileOperationInput):
    file_path: str = Field(..., description="Local path to the file to upload")
    object_name: Optional[str] = Field(None, description="Object name in bucket, defaults to file name")


class DeleteFileInput(FileOperationInput):
    object_name: str = Field(..., description="Object name in bucket")


# ----------------------------
# Helper: Create IBM clients with user-specific credentials
# ----------------------------
def get_ibm_clients(user_id: int, account_name: Optional[str] = None):
    """
    Create IBM Cloud clients using user's credentials from runtime context.
    ユーザーごとの認証情報を runtime.context.credentials から取得して IBM クライアントを作成
    """
    db = SessionLocal()
    credentials = get_configs_dict(db=db, user_id=user_id)
    db.close()
    ibm_accounts = credentials.get("ibm", [])

    creds = next((a for a in ibm_accounts if a["name"] == account_name), None)
    if not creds:
        raise ValueError(f"IBM Cloud account '{account_name}' not found for user.")

    api_key = creds.get("api_key")
    region = creds.get("region", "jp-tok")
    vpc_instance_id = creds.get("vpc_instance_id")

    if not all([api_key, vpc_instance_id]):
        raise ValueError("Incomplete IBM Cloud credentials / IBM認証情報が不完全です")

    # VPC client
    authenticator = IAMAuthenticator(apikey=api_key)
    vpc_client = VpcV1(authenticator=authenticator)
    vpc_client.set_service_url(VpcV1.get_service_url_for_region(region))

    # COS client
    cos_client = ibm_boto3.resource(
        's3',
        ibm_api_key_id=api_key,
        config=Config(signature_version='oauth'),
        endpoint_url=f"https://s3.{region}.cloud-object-storage.appdomain.cloud"
    )

    return vpc_client, cos_client, vpc_instance_id


# ----------------------------
# Helper: retry on auth error
# ----------------------------
def ibm_vpc_operation(func, user_id: int, account_name: Optional[str] = None, *args, **kwargs):
    """
    Operate VPC function with retry on auth error
    認証エラー時は再試行
    """
    try:
        vpc_client, _, vpc_instance_id = get_ibm_clients(user_id, account_name)
        return func(vpc_client, vpc_instance_id, *args, **kwargs)
    except ApiException as e:
        if e.code in (401, 403):
            vpc_client, _, vpc_instance_id = get_ibm_clients(user_id, account_name)
            return func(vpc_client, vpc_instance_id, *args, **kwargs)
        else:
            raise


def ibm_cos_operation(func, user_id: int, account_name: Optional[str] = None, *args, **kwargs):
    """
    Operate COS function with retry on error
    COS操作時にエラーなら再試行
    """
    try:
        _, cos_client, _ = get_ibm_clients(user_id, account_name)
        return func(cos_client, *args, **kwargs)
    except ibm_boto3.exceptions.Boto3Error:
        _, cos_client, _ = get_ibm_clients(user_id, account_name)
        return func(cos_client, *args, **kwargs)


# ----------------------------
# VM Operations
# ----------------------------
async def _list_vms(user_id: int, account_name: Optional[str] = None) -> list[str]:
    """
    Return a list of running VM instances for this user.
    このユーザーの稼働中VMインスタンスのリストを返す
    """
    def _list(client, vpc_id):
        vms = client.list_instances(vpc_id=vpc_id).get_result().get('instances', [])
        return [vm['name'] for vm in vms] or []
    return ibm_vpc_operation(_list, user_id, account_name)


async def _start_vm(user_id: int, vm_name: str, account_name: Optional[str] = None) -> str:
    """
    Start the specified VM instance for this user.
    このユーザーの指定VMを起動
    """
    def _start(client, vpc_id, vm_name):
        vms = client.list_instances(vpc_id=vpc_id).get_result().get('instances', [])
        vm = next((vm for vm in vms if vm['name'] == vm_name), None)
        if not vm:
            return f"VM {vm_name} not found."
        client.create_instance_action(vpc_id=vpc_id, instance_id=vm['id'], type="start")
        return f"VM {vm_name} started."
    return ibm_vpc_operation(_start, user_id, account_name, vm_name)


async def _stop_vm(user_id: int, vm_name: str, account_name: Optional[str] = None) -> str:
    """
    Stop the specified VM instance for this user.
    このユーザーの指定VMを停止
    """
    def _stop(client, vpc_id, vm_name):
        vms = client.list_instances(vpc_id=vpc_id).get_result().get('instances', [])
        vm = next((vm for vm in vms if vm['name'] == vm_name), None)
        if not vm:
            return f"VM {vm_name} not found."
        client.create_instance_action(vpc_id=vpc_id, instance_id=vm['id'], type="stop")
        return f"VM {vm_name} stopped."
    return ibm_vpc_operation(_stop, user_id, account_name, vm_name)


# ----------------------------
# Object Storage Operations
# ----------------------------
async def _list_buckets(user_id: int, account_name: Optional[str] = None) -> list[str]:
    """
    List all buckets in Object Storage for this user.
    このユーザーのObject Storageバケット一覧
    """
    def _list(cos):
        return [b.name for b in cos.buckets.all()] or []
    return ibm_cos_operation(_list, user_id, account_name)


async def _create_bucket(user_id: int, bucket_name: str, account_name: Optional[str] = None) -> str:
    """
    Create a new bucket in Object Storage for this user.
    このユーザー用のObject Storageに新しいバケットを作成
    """
    def _create(cos, name):
        cos.create_bucket(Bucket=name)
        return f"Bucket {name} created."
    return ibm_cos_operation(_create, user_id, account_name, bucket_name)


async def _upload_file_to_bucket(user_id: int, file_path: str, bucket_name: str, object_name: Optional[str], account_name: Optional[str] = None) -> str:
    """
    Upload a local file to the specified IBM Cloud Object Storage bucket for this user.
    このユーザー用のIBM Cloud Storageのバケットにファイルをアップロード
    """
    def _upload(cos, bucket, file_path, obj_name):
        bucket_obj = cos.Bucket(bucket)
        import os
        if not obj_name:
            obj_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            bucket_obj.put_object(Key=obj_name, Body=f)
        return f"File '{obj_name}' uploaded to bucket '{bucket}'."
    return ibm_cos_operation(_upload, user_id, account_name, bucket_name, file_path, object_name)


async def _list_files(user_id: int, account_name: str, bucket_name: str) -> list[str]:
    """
    List all objects in the specified IBM Cloud Object Storage bucket for this user.
    指定バケット内のオブジェクト一覧を返す
    """
    def _list(cos, bucket):
        bucket_obj = cos.Bucket(bucket)
        return [obj.key for obj in bucket_obj.objects.all()] or []

    return ibm_cos_operation(_list, user_id, account_name, bucket_name)


async def _delete_file(user_id: int, account_name: str, bucket_name: str, object_name: str) -> str:
    """
    Delete an object from the specified IBM Cloud Object Storage bucket for this user.
    指定バケットからオブジェクトを削除
    """
    def _delete(cos, bucket, obj_name):
        bucket_obj = cos.Bucket(bucket)
        bucket_obj.Object(obj_name).delete()
        return f"Object '{obj_name}' deleted from bucket '{bucket}'."

    return ibm_cos_operation(_delete, user_id, account_name, bucket_name, object_name)


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
delete_file = tool(_delete_file, args_schema=DeleteFileInput)


def create_ibmcloud_tools() -> list:
    """
    Return a list of IBM Cloud tools for the agent.
    エージェント用のIBM Cloudツールリストを返す
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
    ]
