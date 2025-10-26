
from typing import List, Optional


def get_cloud_tools(providers: Optional[List[str]]):
    """
    Return tools of cloud operations.
    クラウドサービスのツールを返す

    Args:
        providers: List of cloud providers("aws", "azure", "gcp", "ibmcloud").

    Returns:
        tools: LangChain tools of cloud operations
    """
    tools = []
    if "gcp" in providers:
        from tools.gcp_tools import gcp_tools
        tools.extend(gcp_tools)
    if "aws" in providers:
        from tools.aws_tools import aws_tools
        tools.extend(aws_tools)
    if "azure" in providers:
        from tools.azure_tools import azure_tools
        tools.extend(azure_tools)
    if "ibmcloud" in providers:
        from tools.ibmcloud_tools import ibmcloud_tools
        tools.extend(ibmcloud_tools)
    return tools
