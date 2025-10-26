from langchain.tools import tool
from typing import List, Optional
from utils.embedding import Embedding


class RAGToolClass:
    def __init__(self, vectorstore_class="chroma"):
        """
        Initialize RAG tool with the specified vectorstore class.
        RAGツールを指定されたベクターストアで初期化します。
        """
        self.emb = Embedding(vectorstore_class=vectorstore_class)
        self.emb.load_store()

    def add_document(self, file_paths: Optional[List[str]] = None, page_split: bool = False) -> str:
        """
        Add documents to the vectorstore.
        ドキュメントをベクターストアに追加します。

        Args:
            file_paths: List of file paths to add. / 追加するファイルパスのリスト
            page_split: Whether to split pages when loading. / ページ分割するかどうか

        Returns:
            Status message indicating success or failure.
            成功または失敗のステータスメッセージ
        """
        added = self.emb.add_documents(file_paths=file_paths, page_split=page_split)
        if added:
            return f"Files added successfully: {', '.join(file_paths)}"
        else:
            return "Failed to add files."

    @tool(response_format="content_and_artifact")
    def rag_tool(self, query: Optional[str] = None):
        """
        Document retrieval tool.
        文書検索ツール

        Given a query, retrieves relevant information from the stored documents.
        クエリが渡された場合、保存された文書から関連情報を取得します。

        Args:
            query: The search query string. / 検索するクエリ文字列

        Returns:
            Tuple of (serialized retrieved content, list of retrieved document objects)
            (取得した内容の文字列化, 取得した文書オブジェクトのリスト)
        """
        if not query:
            return "Please provide a query.", []

        retrieved_docs = self.emb.vectorstore.similarity_search(query, k=3)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs


def create_rag_tool_instance(vectorstore_class="chroma") -> RAGToolClass:
    """
    Create an instance of RAGToolClass.
    RAGToolClassのインスタンスを作成します。

    Args:
        vectorstore_class: The vectorstore backend to use (default: "chroma").
        使用するベクターストアの種類（デフォルト: "chroma"）

    Returns:
        RAGToolClass instance / RAGToolClassのインスタンス
    """
    return RAGToolClass(vectorstore_class=vectorstore_class)
