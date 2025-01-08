import os

from typing import List, Optional
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


COLLECTION_NAME = os.getenv("COLLECTION_NAME", "test-v1")

CONNECTION_STRING = os.getenv(
    "CONNECTION_STRING",
    "postgresql+psycopg://bhavan:mysecretpassword@localhost:5433/new-db",
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")


class PGVectorStore:
    def __init__(self):
        self.collection_name = COLLECTION_NAME
        self.connection_string = CONNECTION_STRING
        self.embedding_function = OpenAIEmbeddings(model=EMBEDDING_MODEL)

        self.store = self.initialize_store()

    def initialize_store(self):
        return PGVector(
            embeddings=self.embedding_function,
            collection_name=self.collection_name,
            connection=self.connection_string,
            use_jsonb=True,
        )

    def add_documents(self, docs: List[Document]):
        # Adding documents to the vector store
        self.store.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])

    def similarity_search(
        self,
        query: str,
        filter: dict,
        k: Optional[int] = 10,
    ):
        return self.store.similarity_search(
            query,
            k,
            filter,
        )

    def delete_documents(self):
        pass
