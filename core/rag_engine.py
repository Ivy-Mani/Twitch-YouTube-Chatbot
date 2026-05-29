import os
import tempfile
import hashlib
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# Use temp directory for FAISS indexes
PERSIST_DIR = os.path.join(tempfile.gettempdir(), "yt_insight_faiss")
os.makedirs(PERSIST_DIR, exist_ok=True)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_index_path(text: str) -> str:
    """Create unique index path based on content."""
    hash_val = hashlib.md5(text[:500].encode()).hexdigest()
    return os.path.join(PERSIST_DIR, f"faiss_{hash_val}")

def build_vectorstore(text: str, index_path: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split = splitter.split_text(text)
    vectorstore = FAISS.from_texts(
        texts=split,
        embedding=embedding
    )
    # Save to disk
    vectorstore.save_local(index_path)
    return vectorstore

def retrieve(text: str, question: str):
    """Retrieve answer using RAG with FAISS."""
    index_path = get_index_path(text)
    
    # Try to load existing index for THIS video
    try:
        if os.path.exists(index_path):
            vectorstore = FAISS.load_local(
                index_path, 
                embedding,
                allow_dangerous_deserialization=True  # Required for FAISS
            )
            print(f"Loaded existing index: {index_path}")
        else:
            raise FileNotFoundError("Index not found")
    except Exception as e:
        # Create new index for this video
        print(f"Creating new index for: {index_path}")
        vectorstore = build_vectorstore(text, index_path)

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
