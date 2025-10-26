import os
from threading import Lock
from langchain.tools import tool
from pydantic import BaseModel, Field
from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
import ibm_boto3
from ibm_botocore.client import Config
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


# ----------------------------
# IBM Cloud Client Manager
# ----------------------------
class IBMClientManager:
    _vpc_client = None
    _cos_client = None
    _lock = Lock()

    @classmethod
    def get_vpc_client(cls):
        """Get a client for vpc. when it is not created, create a new client."""
        with cls._lock:
            api_key = os.getenv("IBM_API_KEY")
            region = os.getenv("IBM_REGION", "jp-tok")
            if cls._vpc_client is None:
                authenticator = IAMAuthenticator(apikey=api_key)
                client = VpcV1(authenticator=authenticator)
                client.set_service_url(VpcV1.get_service_url_for_region(region))
                cls._vpc_client = client
            return cls._vpc_client

    @classmethod
    def reset_vpc_client(cls):
        with cls._lock:
            cls._vpc_client = None

    @classmethod
    def get_cos_client(cls):
        """Get a client for COS. when it is not created, create a new client."""
        with cls._lock:
            api_key = os.getenv("IBM_API_KEY")
            region = os.getenv("IBM_REGION", "jp-tok")
            if cls._cos_client is None:
                cls._cos_client = ibm_boto3.resource(
                    's3',
                    ibm_api_key_id=api_key,
                    config=Config(signature_version='oauth'),
                    endpoint_url=f"https://s3.{region}.cloud-object-storage.appdomain.cloud"
                )
            return cls._cos_client

    @classmethod
    def reset_cos_client(cls):
        with cls._lock:
            cls._cos_client = None


# ----------------------------
# Helper: automatic retry on Auth error
# ----------------------------
def ibm_vpc_operation(func, *args, **kwargs):
    """Operate VPC function. When failed, retry."""
    try:
        client = IBMClientManager.get_vpc_client()
        return func(client, *args, **kwargs)
    except ApiException as e:
        if e.code in (401, 403):
            IBMClientManager.reset_vpc_client()
            client = IBMClientManager.get_vpc_client()
            return func(client, *args, **kwargs)
        else:
            raise


def ibm_cos_operation(func, *args, **kwargs):
    """Operate COS function. When failed, retry."""
    try:
        client = IBMClientManager.get_cos_client()
        return func(client, *args, **kwargs)
    except ibm_boto3.exceptions.Boto3Error:
        IBMClientManager.reset_cos_client()
        client = IBMClientManager.get_cos_client()
        return func(client, *args, **kwargs)


# ----------------------------
# VM Operations
# ----------------------------
@tool
def list_vms(_: str) -> str:
    """
    Return a list of running VM instances.
    稼働中のVMインスタンスのリストを返す
    """
    vpc_instance_id = os.getenv("IBM_VPC_INSTANCE_ID")

    def _list(client, vpc_id):
        vms = client.list_instances(vpc_id=vpc_id).get_result()['instances']
        return [vm['name'] for vm in vms] or []

    return ibm_vpc_operation(_list, vpc_instance_id)


@tool
def start_vm(vm_name: str) -> str:
    """
    Start the specified VM instance.
    VM起動
    """
    vpc_instance_id = os.getenv("IBM_VPC_INSTANCE_ID")

    def _start(client, vpc_id, vm_name):
        vms = client.list_instances(vpc_id=vpc_id).get_result()['instances']
        vm = next((vm for vm in vms if vm['name'] == vm_name), None)
        if not vm:
            return f"VM {vm_name} not found."
        client.create_instance_action(vpc_id=vpc_id, instance_id=vm['id'], type="start")
        return f"VM {vm_name} started."

    return ibm_vpc_operation(_start, vpc_instance_id, vm_name)


@tool
def stop_vm(vm_name: str) -> str:
    """
    Stop the specified VM instance.
    VM停止
    """
    vpc_instance_id = os.getenv("IBM_VPC_INSTANCE_ID")

    def _stop(client, vpc_id, vm_name):
        vms = client.list_instances(vpc_id=vpc_id).get_result()['instances']
        vm = next((vm for vm in vms if vm['name'] == vm_name), None)
        if not vm:
            return f"VM {vm_name} not found."
        client.create_instance_action(vpc_id=vpc_id, instance_id=vm['id'], type="stop")
        return f"VM {vm_name} stopped."

    return ibm_vpc_operation(_stop, vpc_instance_id, vm_name)


# ----------------------------
# Object Storage Operations
# ----------------------------
@tool
def list_buckets(_: str) -> str:
    """
    List all buckets in Object Storage.
    バケット一覧
    """
    def _list(cos):
        return [b.name for b in cos.buckets.all()] or []
    return ibm_cos_operation(_list)


@tool
def create_bucket(bucket_name: str) -> str:
    """
    Create a new bucket in Object Storage.
    新しいバケットを作成
    """
    def _create(cos, name):
        cos.create_bucket(Bucket=name)
        return f"Bucket {name} created."
    return ibm_cos_operation(_create, bucket_name)


class UploadFileInput(BaseModel):
    file_path: str = Field(..., description="Local path to the file to upload")
    bucket_name: str = Field(..., description="Target ICOS bucket name")
    object_name: Optional[str] = Field(None, description="Object name in bucket, defaults to file name")


@tool(args_schema=UploadFileInput)
def upload_file_to_bucket(file_path: str, bucket_name: str, object_name: str) -> str:
    """
    Upload a local file to the specified IBM Cloud Object Storage bucket.
    指定したIBM Cloud Storageのバケットにファイルをアップロードする
    """
    def _upload(cos, bucket, file_path, obj_name):
        bucket_obj = cos.Bucket(bucket)
        with open(file_path, "rb") as f:
            bucket_obj.put_object(Key=obj_name, Body=f)
        return f"File '{obj_name}' uploaded to bucket '{bucket}'."

    return ibm_cos_operation(_upload, bucket_name, file_path, object_name)


# ----------------------------
# Tool Registration
# ----------------------------
ibmcloud_tools = [
    list_vms,
    start_vm,
    stop_vm,
    list_buckets,
    create_bucket,
    upload_file_to_bucket
]
