from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
# os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"
from dotenv import load_dotenv
load_dotenv()

PERSIST_DIR="./downloads/chroma_db" 
COLLECTION_NAME="my_collection"
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
def buildvectorstore(text:str):
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split=splitter.split_text(text)
    vectorstore = Chroma.from_texts(
        texts=split,
        embedding=embedding,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR  
    )
    return vectorstore

def retrieve(text: str, question: str):
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
            print("Loading existing Chroma DB...")
            vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=embedding,
                persist_directory=PERSIST_DIR
            )
    else:
            vectorstore=buildvectorstore(text)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5}
    )

    docs = retriever.invoke(question)
    context=""
    for doc in docs:
        context=context+doc.page_content
    prompt= PromptTemplate(
        input_variables=["context","question"],
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
    llm=ChatGroq(model="llama-3.3-70b-versatile")
    parser=StrOutputParser()
    chain=prompt|llm|parser
    return chain.invoke({"context":context,"question":question})
    
