from langchain.tools import tool
from typing import Optional
from app.database.database import SessionLocal
from app.services.cloud_config_service import get_configs_dict


def _list_all_cloud_resources(user_id: Optional[int]) -> dict:
    """
    Return a summary json object of all cloud resources (VMs and buckets) across all providers.
    全クラウドのVMとバケットのサマリを返す

    Args:
        providers: List of cloud providers("aws", "azure", "gcp", "ibmcloud").

    Returns:
        Result of cloud resources, structured JSON:
            {
                "AWS": {"vms": [...], "buckets": [...]},
                "Azure": {"vms": [...], "buckets": [...]},
                ...
            }
    """
    db = SessionLocal()
    credentials = get_configs_dict(db=db, user_id=user_id)
    db.close()

    summary = {}
    if "aws" in credentials:
        summary["aws"] = []
        from tools.aws_tools import _list_vms as aws_list_vms, _list_buckets as aws_list_buckets
        for credential in credentials.get("aws"):
            try:
                summary_item = {
                    "vms": aws_list_vms(user_id, credential["name"]),
                    "buckets": aws_list_buckets(user_id, credential["name"]),
                }
            except Exception as e:
                summary_item = {"error": str(e)}
            summary["aws"].append(summary_item)

    if "azure" in credentials:
        from tools.azure_tools import _list_vms as azure_list_vms, _list_buckets as azure_list_buckets
        for credential in credentials.get("azure"):
            try:
                summary_item = {
                    "vms": azure_list_vms(user_id, credential["name"]),
                    "buckets": azure_list_buckets(user_id, credential["name"]),
                }
            except Exception as e:
                summary_item = {"error": str(e)}
            summary["azure"].append(summary_item)

    if "gcp" in credentials:
        from tools.gcp_tools import _list_vms as gcp_list_vms, _list_buckets as gcp_list_buckets
        for credential in credentials.get("gcp"):
            try:
                summary_item = {
                    "vms": gcp_list_vms(user_id, credential["name"]),
                    "buckets": gcp_list_buckets(user_id, credential["name"]),
                }
            except Exception as e:
                summary_item = {"error": str(e)}
            summary["gcp"].append(summary_item)

    if "ibmcloud" in credentials:
        from tools.ibmcloud_tools import _list_vms as ibm_list_vms, _list_buckets as ibm_list_buckets
        for credential in credentials.get("ibm"):
            try:
                summary_item = {
                    "vms": ibm_list_vms(user_id, credential["name"]),
                    "buckets": ibm_list_buckets(user_id, credential["name"]),
                }
            except Exception as e:
                summary_item = {"error": str(e)}
            summary["ibm"].append(summary_item)

    return summary


list_all_cloud_resources = tool(_list_all_cloud_resources)
