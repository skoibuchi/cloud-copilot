from langchain.tools import tool
from typing import List, Optional


@tool
def list_all_cloud_resources(providers: Optional[List[str]]) -> dict:
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

    summary = {}
    if "aws" in providers:
        from tools.aws_tools import list_vms as aws_list_vms, list_buckets as aws_list_buckets
        try:
            summary["AWS"] = {
                "vms": aws_list_vms(""),
                "buckets": aws_list_buckets(""),
            }
        except Exception as e:
            summary["AWS"] = {"error": str(e)}

    if "azure" in providers:
        from tools.azure_tools import list_vms as azure_list_vms, list_buckets as azure_list_buckets
        try:
            summary["Azure"] = {
                "vms": azure_list_vms(""),
                "buckets": azure_list_buckets(""),
            }
        except Exception as e:
            summary["Azure"] = {"error": str(e)}

    if "gcp" in providers:
        from tools.gcp_tools import list_vms as gcp_list_vms, list_buckets as gcp_list_buckets
        try:
            summary["GCP"] = {
                "vms": gcp_list_vms(""),
                "buckets": gcp_list_buckets(""),
            }
        except Exception as e:
            summary["GCP"] = {"error": str(e)}

    if "ibmcloud" in providers:
        from tools.ibmcloud_tools import list_vms as ibm_list_vms, list_buckets as ibm_list_buckets
        try:
            summary["IBMCloud"] = {
                "vms": ibm_list_vms(""),
                "buckets": ibm_list_buckets(""),
            }
        except Exception as e:
            summary["IBMCloud"] = {"error": str(e)}

    return summary
