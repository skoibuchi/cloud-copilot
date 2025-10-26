from utils.embedding import supported_vectorstore_class
from tools.memory_tools import get_memory_tools
from tools.multi_cloud_tools import list_all_cloud_resources
from tools.utils import get_cloud_tools


def get_tools(providers: str, vectorstore_class: str = "chroma"):
    _providers = [provider.lower() for provider in providers.split(',')]
    tools = []

    # memory
    tools.extend(get_memory_tools())

    # cloud
    tools.extend(get_cloud_tools(providers=_providers))
    tools.append(list_all_cloud_resources)

    # vectorstore
    rag_tool_instance = None
    if vectorstore_class in supported_vectorstore_class:
        from tools.rag_tools import create_rag_tool_instance
        rag_tool_instance = create_rag_tool_instance(vectorstore_class=vectorstore_class)
        tools.append(rag_tool_instance.rag_tool)

    return tools, rag_tool_instance