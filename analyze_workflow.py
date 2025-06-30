# analyze_workflow.py

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

db = FAISS.load_local("faiss_index", OpenAIEmbeddings())
retriever = db.as_retriever()
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

def analyze_workflow(yaml_content):
    prompt = f"""
You are a GitHub Actions expert.

Analyze the following workflow. Refer only to your internal documents. 
Say either PREDICTION: PASS or PREDICTION: FAIL, and explain your reasoning.

Workflow:
{yaml_content}
"""
    return qa.run(prompt)

# Example usage:
if __name__ == "__main__":
    with open(".github/workflows/main-ci.yml", "r") as f:
        yaml_content = f.read()

    response = analyze_workflow(yaml_content)
    print("🔍 Analysis Result:")
    print(response)
