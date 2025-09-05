# ref service context: https://medium.aiplanet.com/advanced-rag-using-llama-index-e06b00dc0ed8
# ref document https://medium.com/@abul.aala.fareh/customizing-documents-in-llamaindex-357de97d3917

from llama_index.core import Document,SimpleDirectoryReader,ServiceContext,VectorStoreIndex
from llama_index.core.schema import MetadataMode

document = Document(
    text="This is a super-customized document",
    metadata={
        "file_name": "super_secret_document.txt",
        "category": "finance",
        "author": "LlamaIndex",
    },
  

  # Once your metadata is converted into a string using metadata_seperator
  # and metadata_template, the metadata_templates controls what that metadata
  # looks like when joined with the text content 

    excluded_llm_metadata_keys=["file_name"],
    metadata_seperator="::",
    metadata_template="{key}=>{value}",
    text_template="Metadata: {metadata_str}\n-----\nContent: {content}",
)

print("The LLM sees this: \n",document.get_content(metadata_mode=MetadataMode.LLM),)
print("The Embedding model sees this: \n", document.get_content(metadata_mode=MetadataMode.EMBED),)

# configure embedding model
from llama_index.core.embeddings import resolve_embed_model
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding 
#embed_model = resolve_embed_model("local:BAAI/bge-large-en-v1.5")
# embed_model = HuggingFaceInferenceAPIEmbedding(model_name="BAAI/bge-large-en-v1.5",)

embed_model = HuggingFaceInferenceAPIEmbedding(
    model_name="http://192.168.3.26:8083",
    token="HF_TOKEN",
    provider="auto",  # this will use the best provider available
)
test_embeds = embed_model.get_text_embedding("Hello World!")


documents = SimpleDirectoryReader(
    input_files=[r"D:\temp\embedding\pdf\abc.pdf"]
).load_data()

#create senetence window node parser with default settings
from llama_index.core.node_parser import SentenceWindowNodeParser,SimpleNodeParser
sentence_node_parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,
    window_metadata_key="window",
    original_text_metadata_key="original_text")
#base_node_parser = SentenceSplitter(llm=llm)
base_node_parser = SimpleNodeParser()
#

# 
base_nodes = base_node_parser.get_nodes_from_documents(documents)
print(f"BASE NODES :\n {base_nodes[4]}")

# 
nodes = sentence_node_parser.get_nodes_from_documents(documents)
print(f"SENTENCE NODES :\n {nodes[4]}")

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

Settings.llm = OpenAI(model="gpt-3.5-turbo")
Settings.embed_model = embed_model #OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900

# a vector store index only needs an embed model
index = VectorStoreIndex.from_documents(documents, embed_model=embed_model #, transformations=transformations
)

from llama_index.core import SimpleDirectoryReader, StorageContext
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore
import textwrap

import psycopg2

connection_string = "postgresql://postgres:password@localhost:5432"
db_name = "embedding_db"
# conn = psycopg2.connect(connection_string)
# conn.autocommit = True

# with conn.cursor() as c:
#     c.execute(f"DROP DATABASE IF EXISTS {db_name}")
#     c.execute(f"CREATE DATABASE {db_name}")

vector_store = PGVectorStore.from_params(
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

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
query_engine = index.as_query_engine()
# sentence_index = VectorStoreIndex(
#     nodes,
#     service_context=ctx_sentence)
# base_index = VectorStoreIndex(
#     base_nodes,
#     service_context=ctx_base)


# ... until you create a query engine
# query_engine = index.as_query_engine(llm=llm)

# # ==============================
# ctx_sentence = ServiceContext.from_defaults(
#     llm=None,
#     embed_model=embed_model,
#     node_parser=nodes)
# # The above has SentenceWindowNodeParser incorporated
# #
# ctx_base = ServiceContext.from_defaults(
#     llm=None,
#     embed_model=embed_model,
#     node_parser=base_nodes)

print("end")
