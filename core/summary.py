from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
load_dotenv()
def summary(transcript:str):
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )
    docsplit=splitter.split_text(transcript)
    
    prompt = PromptTemplate(
        input_variables=[ "text"],
        template="Summarize this:\n\n{text}"
    )

    llm=ChatGroq(model="llama-3.3-70b-versatile")
    parser=StrOutputParser()
    chain=prompt|llm|parser

    final_summ=""
    for docs in docsplit:
        summ=chain.invoke({"text":docs})
        final_summ=final_summ+summ

    prompt_1=PromptTemplate(
        input_variables=['final_summ'],
        template="""You are an  exprt summarizer.Summarize all the list of summaries in one single summary . It should be easy to understand.Donot add any preamble.\n\n{final_summ}"""
    )
    chain_2=prompt_1|llm|parser
    return chain_2.invoke({"final_summ":final_summ})


def title(final_summ:str):
    prompt = PromptTemplate(
        input_variables=[ "final_summ"],
        template="YOU ARE A TITLE EXPERT.GIVE ME A VERY APPROPRIATE TITLE.Donot add any preamble:\n\n{final_summ}"
    )
    llm=ChatGroq(model="llama-3.3-70b-versatile")
    parser=StrOutputParser()
    chain=prompt|llm|parser
    return chain.invoke({"final_summ":final_summ})
