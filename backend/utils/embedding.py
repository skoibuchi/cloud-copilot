import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_community.document_loaders import BSHTMLLoader
# from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_community.document_loaders import TextLoader as TextFileLoader
# from langchain_text_splitter import HTMLHeaderTextSplitter
# from langchain_text_splitter import CharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.vectorstores import Milvus
from typing import List


# supported file extension
supported_file_types = ['.pdf', '.html', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt']
# supported vectorstore
supported_vectorstore_class = ['chroma', 'faiss', 'milvus']


class PDFLoader:
    def __init__(self, file_path):
        self.loader = PyPDFLoader(file_path)
        self.text_splitter = None


class HTMLLoader:
    def __init__(self, file_path):
        self.loader = BSHTMLLoader(file_path)
        self.text_splitter = RecursiveCharacterTextSplitter(
            # separators=['\n\n', '\n', ' ', ''],
            chunk_size=2000,
            chunk_overlap=20,
            is_separator_regex=False,
        )


class WordLoader:
    def __init__(self, file_path, mode='single'):
        self.loader = Docx2txtLoader(file_path)
        self.text_splitter = None


class PowerPointLoader:
    def __init__(self, file_path, mode='single'):
        self.loader = UnstructuredPowerPointLoader(file_path, mode=mode)
        self.text_splitter = None


class ExcelLoader:
    def __init__(self, file_path, mode='single'):
        self.loader = UnstructuredExcelLoader(file_path, mode=mode)
        self.text_splitter = None


class TextLoader:
    def __init__(self, file_path):
        self.loader = TextFileLoader(file_path)
        self.text_splitter = RecursiveCharacterTextSplitter(
            # separators=['\n\n', '\n', ' ', ''],
            chunk_size=300,
            chunk_overlap=20,
            is_separator_regex=False,
        )


# TODO not tested for Milvus
class Embedding:
    def __init__(self, embeddings=HuggingFaceEmbeddings(), vectorstore_class='faiss', connection_args={}, use_saved_store=True):
        self.embeddings = embeddings
        self.vectorstore_class = vectorstore_class.lower()
        self.persist_directory = './vectorstore_' + self.vectorstore_class
        if not use_saved_store and os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        self.vectorstore = None
        if self.vectorstore_class == 'faiss':
            if os.path.exists(self.persist_directory):
                self.load_store()
            else:
                dummy_text, dummy_id = '1', 1
                self.vectorstore = FAISS.from_texts(texts=[dummy_text], embedding=self.embeddings, ids=[dummy_id])
                self.vectorstore.delete([dummy_id])
        elif self.vectorstore_class == 'chroma':
            self.vectorstore = Chroma(embedding_function=embeddings, persist_directory=self.persist_directory)
        elif self.vectorstore_class == 'milvus':
            self.milvus_collection_name = 'LangChainCollection'
            self.milvus_connection_args = {
                'host': connection_args.get('host', ''),
                'port': connection_args.get('port', ''),
                'user': connection_args.get('user', ''),
                'password': connection_args.get('password', ''),
                'server_pem_path': connection_args.get('server_pem_path', ''),
                'secure': connection_args.get('secure', False),
                'server_name': connection_args.get('server_name', '')
            }
            self.vectorstore = Milvus(
                embeddings=self.embeddings,
                connection_args=self.milvus_connection_args,
                drop_old=True,
                collection_name=self.milvus_collection_name
            )

    def get_loader(self, file_path):
        ext = os.path.splitext(file_path)[1]
        if ext not in supported_file_types:
            return None

        if ext == '.pdf':
            return PDFLoader(file_path=file_path)
        elif ext == '.html':
            return HTMLLoader(file_path=file_path)
        elif ext == '.doc' or ext == '.docx':
            return WordLoader(file_path=file_path)
        elif ext == '.ppt' or ext == '.pptx':
            return PowerPointLoader(file_path=file_path)
        elif ext == '.xls' or ext == '.xlsx':
            return ExcelLoader(file_path=file_path)
        elif ext == '.txt':
            return TextLoader(file_path=file_path)
        # TODO implement other extensions

        return None

    # build vectorstore with files
    def load_files(self, file_paths: List[str] = [], page_split: bool = False):
        loader_classes = [self.get_loader(file_path=file_path) for file_path in file_paths if self.get_loader(file_path=file_path)]
        documents = []
        for loader_class in loader_classes:
            documents.extend(loader_class.loader.load_and_split(text_splitter=loader_class.text_splitter) if page_split else loader_class.loader.load())

        if self.vectorstore_class == 'faiss':
            self.vectorstore = FAISS.from_documents(documents=documents, embedding=self.embeddings)
        elif self.vectorstore_class == 'chroma':
            self.vectorstore = Chroma.from_documents(documents=documents, embedding=self.embeddings, persist_directory=self.persist_directory)
        elif self.vectorstore_class == 'milvus':
            self.vectorstore = Milvus.from_documents(
                documents=documents,
                embeddings=self.embeddings,
                connection_args=self.milvus_connection_args,
                drop_old=True,
                collection_name=self.milvus_collection_name
            )

    # build vectorstore with texts
    def load_texts(self, texts: List[str] = [], metadatas: List[dict] = None, ids: List[str] = None):
        if self.vectorstore_class == 'faiss':
            self.vectorstore = FAISS.from_texts(texts=texts, embedding=self.embeddings, metadatas=metadatas, ids=ids)
        elif self.vectorstore_class == 'chroma':
            self.vectorstore = Chroma.from_texts(texts=texts, embedding=self.embeddings, metadatas=metadatas, ids=ids, persist_directory=self.persist_directory)
        elif self.vectorstore_class == 'milvus':
            self.vectorstore = Milvus.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas,
                connection_args=self.milvus_connection_args,
                drop_old=True,
                collection_name=self.milvus_collection_name
            )

    # add files
    def add_documents(self, file_paths: List[str], page_split: bool = False):
        loader_classes = [self.get_loader(file_path=file_path) for file_path in file_paths if self.get_loader(file_path=file_path)]
        documents = []
        for loader_class in loader_classes:
            documents.extend(loader_class.loader.load_and_split(text_splitter=loader_class.text_splitter) if page_split else loader_class.loader.load())
        res = self.vectorstore.add_documents(documents=documents)
        if not res:
            return False
        return True

    # テキスト追加読み込み
    def add_texts(self, texts: List[str] = [], metadatas: List[dict] = None, ids: List[str] = None):
        res = self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        if not res:
            return False
        return True

    # なんかFAISSの時だけ必要っぽい
    # vectorsotre保存
    def save_store(self):
        if self.vectorstore:
            if self.vectorstore_class == 'faiss':
                self.vectorstore.save_local(self.persist_directory)
                return True
            elif self.vectorstore_class == 'chroma':
                # Since Chroma 0.4.x the manual persistence method is no longer supported as docs are automatically persisted.
                # self.vectorstore.persist()
                return True
            elif self.vectorstore_class == 'milvus':
                return True
            else:
                return False
        return False

    def load_store(self):
        if not self.vectorstore:
            if self.vectorstore_class == 'faiss':
                self.vectorstore = FAISS.load_local(folder_path=self.persist_directory, embeddings=self.embeddings)
            elif self.vectorstore_class == 'chroma':
                self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            elif self.vectorstore_class == 'milvus':
                self.vectorstore = Milvus(
                    embeddings=self.embeddings,
                    connection_args=self.milvus_connection_args,
                    collection_name=self.milvus_collection_name
                )
            return True
        return False

    def get_similarity_search(self, query: str):
        if self.vectorstore:
            return self.vectorstore.similarity_search(query)
        return None

    def get_all_documents(self):
        res = []
        if self.vectorstore:
            if self.vectorstore_class == 'faiss':
                docs = self.vectorstore.docstore.__dict__
                for key, value in docs['_dict'].items():
                    source = value.metadata['source']
                    page = -1
                    ext = os.path.splitext(source)[1]
                    if ext == '.pdf':
                        page = value.metadata.get('page', -1)
                    elif ext in {'.doc', '.docx', '.ppt', '.pptx', 'xls', 'xlsx'}:
                        page = value.metadata.get('page_number', -1)
                    page_name = ''
                    if ext in {'.xls', '.xlsx'}:
                        page_name = value.metadata.get('page_name', '')
                    res.append(
                        {
                            'id': key,
                            'source': source,
                            'page': page,
                            'content': value.page_content,
                            'page_name': page_name
                        }
                    )
            elif self.vectorstore_class == 'chroma':
                docs = self.vectorstore.get()
                for id, metadata, document in zip(docs['ids'], docs['metadatas'], docs['documents']):
                    source = metadata['source']
                    page = -1
                    ext = os.path.splitext(source)[1]
                    if ext == '.pdf':
                        page = metadata.get('page', -1)
                    elif ext in {'.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'}:
                        page = metadata.get('page_number', -1)
                    page_name = ''
                    if ext in {'.xls', '.xlsx'}:
                        page_name = metadata.get('page_name', '')
                    res.append(
                        {
                            'id': id,
                            'source': source,
                            'page': page,
                            'content': document,
                            'page_name': page_name
                        }
                    )
            elif self.vectorstore_class == 'milvus':
                # 取得する方法調査中 get_pksで直接idを取って来れるが
                pass
        return res

    def get_document_ids_from_source(self, filename):
        ids = []
        if self.vectorstore_class in {'faiss', 'chroma'}:
            docs = self.get_all_documents()
            for doc in docs:
                if doc['source'] == filename:
                    ids.append(doc['id'])
        elif self.vectorstore_class == 'milvus':
            ids = self.vectorstore.get_pks('source == {filename}'.format(filename=filename))
        return ids

    def delete_documents_from_ids(self, ids):
        return self.vectorstore.delete(ids)

    def delete_document_from_source(self, filename):
        ids = self.get_document_ids_from_source(filename)
        return self.delete_documents_from_ids(ids)
