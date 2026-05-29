import os
import tempfile
import hashlib
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# Use temp directory that persists across sessions but not across videos
PERSIST_DIR = os.path.join(tempfile.gettempdir(), "yt_insight_chroma_db")
os.makedirs(PERSIST_DIR, exist_ok=True)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_collection_name(text: str) -> str:
    """Create unique collection name based on content."""
    # Use hash of first 500 chars as unique identifier for this video
    return f"coll_{hashlib.md5(text[:500].encode()).hexdigest()}"

def buildvectorstore(text: str, collection_name: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split = splitter.split_text(text)
    vectorstore = Chroma.from_texts(
        texts=split,
        embedding=embedding,
        collection_name=collection_name,
        persist_directory=PERSIST_DIR  
    )
    return vectorstore

def retrieve(text: str, question: str):
    """Retrieve answer using RAG. Creates NEW vectorstore for each video."""
    collection_name = get_collection_name(text)
    
    # Try to load existing collection for THIS video only
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=PERSIST_DIR
        )
        # Test if collection exists by trying a search
        test_docs = vectorstore.similarity_search("test", k=1)
        print(f"Loaded existing collection: {collection_name}")
    except Exception as e:
        # Collection doesn't exist - create new one for this video
        print(f"Creating new collection for: {collection_name}")
        vectorstore = buildvectorstore(text, collection_name)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5}
    )

    docs = retriever.invoke(question)
    context = " ".join([doc.page_content for doc in docs])
    
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template = """You are a helpful assistant that answers questions strictly based on the provided context.

## Instructions
- Answer ONLY using information from the context below
- If the answer isn't in the context, respond: "I don't have enough information in the provided context to answer this question."
- Be concise, accurate, and cite relevant parts of the context when possible
- Never hallucinate or infer beyond what the context states

## Context
{context}

## Question
{question}

## Answer
"""
    )
    llm = ChatGroq(model="llama-3.3-70b-versatile")
    parser = StrOutputParser()
    chain = prompt | llm | parser
    return chain.invoke({"context": context, "question": question})
