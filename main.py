from core.rag_engine import retrieve
from utils.audioprocesser import process_input
from core.summary import summary,title
from core.transcriber import transcript_extraction

caption=""
def run_pipeline(source:str):
    global caption 
    chunk_path=process_input(source)
    caption=transcript_extraction(chunk_path)
    summ=summary(caption)
    heading=title(summ)
    print(f"{heading}\n\n {summ}")

def ques_ans():
    print('ENTER YOUR DESIRED QUESTION ?.PRESS EXIT TO END COVERSATION.\n\n')
    ques=""
    while("exit" not in ques.lower()):
        ques=input('Enter your question:')
        ans=retrieve(caption,ques)
        print(ans)


#main
link = input("Enter the YouTube link: ")
run_pipeline(link)
ques_ans()





    


    
