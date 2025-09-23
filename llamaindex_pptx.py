
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
from pathlib import Path
import glob2
from langchain_community.document_loaders import UnstructuredPowerPointLoader

# ref: https://docs.llamaindex.ai/en/stable/examples/vector_stores/postgres 
import psycopg2

from llama_index.vector_stores.postgres import PGVectorStore
import psycopg2
import json

from langchain.schema import Document

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
                (id, embedding, text, metadata_,node_id, external_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                # Execute with custom parameters
                cursor.execute(
                    query,
                    (
                        numeric_id,
                        node.embedding,
                        node.text,
                        json.dumps(node.metadata),
                        node.id_,
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



# configure embedding model
from llama_index.core.embeddings import resolve_embed_model
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding 
#embed_model = resolve_embed_model("local:BAAI/bge-large-en-v1.5")
# embed_model = HuggingFaceInferenceAPIEmbedding(model_name="BAAI/bge-large-en-v1.5",)

model_url = "http://192.168.3.26:8083"  # kali
model_url = "http://192.168.3.38:8086"  # docker mitm

embed_model = HuggingFaceInferenceAPIEmbedding(
    model_name=model_url,
    token="HF_TOKEN",
    provider="auto",  # this will use the best provider available
)
# test_embeds = embed_model.get_text_embedding("Hello World!")


# documents = SimpleDirectoryReader(
#     input_files=[r"D:\temp\embedding\pdf\AI_Servicesv02b.pdf"]
# ).load_data()


#create senetence window node parser with default settings
# from llama_index.core.node_parser import SentenceWindowNodeParser,SimpleNodeParser
# sentence_node_parser = SentenceWindowNodeParser.from_defaults(
#     window_size=3,
#     window_metadata_key="window",
#     original_text_metadata_key="original_text")
# #base_node_parser = SentenceSplitter(llm=llm)
# base_node_parser = SimpleNodeParser()
# #

# # 
# base_nodes = base_node_parser.get_nodes_from_documents(docs)
# print(f"BASE NODES :\n {base_nodes[0]}")

# # 
# nodes = sentence_node_parser.get_nodes_from_documents(docs)
# print(f"SENTENCE NODES :\n {nodes[0]}")

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

# =====================
#

# get all files
for file_path in Path(r"D:\temp\rag\pptx").glob("*.pptx"):
    # new_path = Path("archive") / file_path.name
    # file_path.replace(new_path)
    loader = UnstructuredPowerPointLoader(file_path,mode="elements")
    docs = loader.load()

    # convert langchain document to Llamaindeex Document
    llamaDocs = [LlamaDocument.from_langchain_format(doc=document) for document in docs]
    # documents = [doc.to_langchain_format() for doc in data]

    # ref advanced powerpoint: https://blog.stackademic.com/unstructured-data-processing-with-langchain-extracting-insights-from-powerpoint-presentations-a4ec770efe52

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(llamaDocs, storage_context=storage_context, show_progress=True)


# query_engine = index.as_query_engine()

print("end")

from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.query_engine import CitationQueryEngine

# 1. Load data
# documents = SimpleWebPageReader(html_to_text=True).load_data(["<<!nav>>https://en.wikipedia.org/wiki/South_Africa<<!/nav>>"])

# 2. Create VectorStoreIndex
# index = VectorStoreIndex.from_documents(documents)

# 3. Create a query engine that preserves citations
# Use a ContextChatEngine to wrap the index's retriever for chat capabilities
chat_engine_with_citations = CitationQueryEngine(
    query_engine=index.as_chat_engine(retriever_mode="default"),
    # Adjust this to get the desired citation details
    metadata_mode="all",
)

# 4. Use the chat engine
response = chat_engine_with_citations.chat("Tell me about UAV.")
print(response)
print("end")
