from app.utils.embedding import supported_vectorstore_class
from app.tools.memory_tools import get_memory_tools
from app.tools.multi_cloud_tools import list_all_cloud_resources
from app.tools.aws_tools import create_aws_tools
from app.tools.gcp_tools import create_gcp_tools
from app.tools.azure_tools import create_azure_tools
from app.tools.ibmcloud_tools import create_ibmcloud_tools


def get_tools(user: str, vectorstore_class: str):
    tools = []

    # memory
    tools.extend(get_memory_tools())

    # cloud
    for t in create_aws_tools():
        tools.append(lambda runtime, t=t: t(runtime=runtime))

    for t in create_azure_tools():
        tools.append(lambda runtime, t=t: t(runtime=runtime))

    for t in create_gcp_tools():
        tools.append(lambda runtime, t=t: t(runtime=runtime))

    for t in create_ibmcloud_tools():
        tools.append(lambda runtime, t=t: t(runtime=runtime))
    tools.append(list_all_cloud_resources)

    # vectorstore
    rag_tool_instance = None
    if vectorstore_class in supported_vectorstore_class:
        from tools.rag_tools import create_rag_tool_instance
        rag_tool_instance = create_rag_tool_instance(vectorstore_class=vectorstore_class, user=user)
        tools.append(rag_tool_instance.rag_tool)

    return tools, rag_tool_instance
