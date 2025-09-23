from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.query_engine import CitationQueryEngine


# ref service context: https://medium.aiplanet.com/advanced-rag-using-llama-index-e06b00dc0ed8
# ref document https://medium.com/@abul.aala.fareh/customizing-documents-in-llamaindex-357de97d3917

from llama_index.core import Document,SimpleDirectoryReader,ServiceContext,VectorStoreIndex
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core import Document as LlamaDocument 
from llama_index.core import SimpleDirectoryReader, StorageContext
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore
import textwrap

from langchain_community.document_loaders import UnstructuredPowerPointLoader

# ref: https://docs.llamaindex.ai/en/stable/examples/vector_stores/postgres 
import psycopg2

from llama_index.vector_stores.postgres import PGVectorStore
import psycopg2
import json

from langchain.schema import Document

# configure embedding model
from llama_index.core.embeddings import resolve_embed_model
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding 

class CustomPGVectorStore(PGVectorStore):
    def __init__(self, connection_string=None, table_name="vectorstore", **kwargs):
        super().__init__(connection_string=connection_string, table_name=table_name, **kwargs)
        # Store connection parameters for later use
        self.connection_string = connection_string
        self.table_name = f"data_{table_name}"
    
    def add(self, nodes, **add_kwargs):
        """Override to add custom columns during insert."""

        conn = psycopg2.connect('postgresql://dev_user:dev_password@192.168.3.38:5431/embedding_db') #self.connection_string)
        cursor = conn.cursor()

        node_ids = []  # Collect node IDs to return

        try:
            for idx, node in enumerate(nodes):
                # Store the node ID for return value
                node_ids.append(node.id_)

                # Extract values for custom columns from node
                external_id = node.metadata.get("page_table", None)
                # embeddingqueue_id = node.metadata.get("embeddingqueue_id", None)

                # Remove from metadata to avoid duplication
                if "external_id" in node.metadata:
                    del node.metadata["external_id"]
                
                # if "embeddingqueue_id" in node.metadata:
                #     del node.metadata["embeddingqueue_id"]

                # Generate a numeric ID based on current timestamp and index
                # This ensures uniqueness while being compatible with bigint type
                import time
                numeric_id = int(time.time() * 1000) + idx

                # Create custom insert query using %s placeholders instead of $n
                query = f"""
                INSERT INTO {self.table_name} 
                (id, embedding, text, metadata_, external_id) 
                VALUES (%s, %s, %s, %s, %s)
                """
                
                # Execute with custom parameters
                cursor.execute(
                    query,
                    (
                        numeric_id,
                        node.embedding,
                        node.text,
                        json.dumps(node.metadata),
                        external_id
                    )
                )
            conn.commit()
            return node_ids
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()


model_url = "http://192.168.3.26:8083"  # kali
model_url = "http://192.168.3.38:8086"  # docker mitm

embed_model = HuggingFaceInferenceAPIEmbedding(
    model_name=model_url,
    token="HF_TOKEN",
    provider="auto",  # this will use the best provider available
)

Settings.llm = None
Settings.embed_model = embed_model #OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900

# a vector store index only needs an embed model
# index = VectorStoreIndex.from_documents(docs, embed_model=embed_model) #, transformations=transformations

# connection_string = "postgresql://postgres:password@localhost:5432"
db_name = "embedding_db"
vector_store = CustomPGVectorStore.from_params(
    database=db_name,
    host="192.168.3.38",
    password="dev_password",
    port="5431",
    user="dev_user",
    table_name="my_emb_tbl",
    embed_dim=1024,  # openai embedding dimension
    hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
        "hnsw_dist_method": "vector_cosine_ops",
    },
)

# ref https://www.llamaindex.ai/blog/building-a-fully-open-source-retriever-with-nomic-embed-and-llamaindex-fc3d7f36d3e4



# service_context = ServiceContext.from_defaults(embed_model=embed_model)

# storage_context = StorageContext.from_defaults(vector_store=vector_store)
# index = VectorStoreIndex.from_documents(storage_context=storage_context, show_progress=True)
# search_query_retriever = index.as_retriever(service_context=service_context, similarity_top_k=1)

query_str = "what are the project objectives"
query_embedding = embed_model.get_query_embedding(query_str)
# construct vector store query
from llama_index.core.vector_stores import VectorStoreQuery

query_mode = "default"
# query_mode = "sparse"
# query_mode = "hybrid"

vector_store_query = VectorStoreQuery(
    query_embedding=query_embedding, similarity_top_k=2, mode=query_mode
)

# returns a VectorStoreQueryResult
query_result = vector_store.query(vector_store_query)
print(query_result)
print("end")
