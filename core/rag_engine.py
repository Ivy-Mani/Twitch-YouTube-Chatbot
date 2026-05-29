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

# Use persistent directory that won't be deleted
PERSIST_DIR = os.path.join(tempfile.gettempdir(), "yt_insight_chroma_db")
os.makedirs(PERSIST_DIR, exist_ok=True)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_collection_name(text: str) -> str:
    """Create unique collection name based on content."""
    return f"collection_{hashlib.md5(text[:500].encode()).hexdigest()}"

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
    collection_name = get_collection_name(text)
    
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embedding,
                persist_directory=PERSIST_DIR
            )
            # Test if collection exists
            vectorstore.similarity_search("test", k=1)
        except:
            vectorstore = buildvectorstore(text, collection_name)
    else:
        vectorstore = buildvectorstore(text, collection_name)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5}
    )

    docs = retriever.invoke(question)
    context = ""
    for doc in docs:
        context = context + doc.page_content
    
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template = """You are a helpful assistant that answers questions strictly based on the provided context.

        ## Instructions
        - Answer ONLY using information from the context below
        - If the answer isn't in the context, respond: "I don't have enough information in the provided context to answer this question."
        - Be concise, accurate, and cite relevant parts of the context when possible
        - If the question is partially answerable, provide what you can and note the gap
        - Respond to greetings naturally and politely
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
