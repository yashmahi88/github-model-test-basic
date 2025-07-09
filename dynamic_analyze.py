import argparse
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader

# --- Argument Parser ---
parser = argparse.ArgumentParser(description="Predict outcome of GitHub Actions workflow")
parser.add_argument('--workflow', required=True, help='Path to the GitHub workflow .yml file')
parser.add_argument('--knowledge', required=True, help='Path to the knowledge .txt file')
parser.add_argument('--query', required=True, help='Prompt to run')
parser.add_argument('--output', default='prediction_output.txt', help='Output file path')
args = parser.parse_args()

# --- Load and chunk knowledge ---
loader = TextLoader(args.knowledge)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = FAISS.from_documents(chunks, embedding)

# --- Load target workflow content ---
with open(args.workflow, 'r') as f:
    workflow_text = f.read()

# --- Run RAG Query ---
query = f"{args.query}\n\n{workflow_text}"
llm = Ollama(model="llama2")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=vector_db.as_retriever())
result = qa.run(query)

# --- Output ---
print("Prediction:", result)
with open(args.output, 'w') as f:
    f.write(result)
