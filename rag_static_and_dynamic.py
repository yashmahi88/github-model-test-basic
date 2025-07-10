# scripts/rag_predict.py

import argparse
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama

# --- Parse CLI args ---
parser = argparse.ArgumentParser()
parser.add_argument("--workflow", required=True)
parser.add_argument("--knowledge_folder", required=True)  # space-separated folders
parser.add_argument("--query_type", required=True, choices=["rule-extraction", "final-analysis"])
parser.add_argument("--batch_file", required=True)
parser.add_argument("--output_file", default="rag_result.txt")
args = parser.parse_args()

# --- Load knowledge documents ---
all_folders = args.knowledge_folder.split()
docs = []
for folder in all_folders:
    folder_path = Path(folder)
    for file in folder_path.rglob("*.*"):
        if file.suffix in [".txt", ".md", ".yml", ".json"]:
            loader = TextLoader(str(file))
            docs.extend(loader.load())

# --- Create vector store ---
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embedding)
retriever = vectorstore.as_retriever()

# --- Load input files ---
workflow_content = Path(args.workflow).read_text()
batch_content = Path(args.batch_file).read_text() if Path(args.batch_file).exists() else ""

# --- Build the prompt ---
if args.query_type == "rule-extraction":
    prompt = f"""
TASK: Extract workflow analysis rules from the knowledge base content below.

TARGET WORKFLOW:
{workflow_content}

INSTRUCTIONS:
1. Find rules/patterns that relate to GitHub Actions workflows
2. Focus on rules mentioning any keywords in the workflow
3. Extract rules about success/failure conditions
4. Format each rule as: "RULE: [description] | TYPE: [PASS/FAIL/WARNING] | SOURCE: [filename]"
5. Only extract rules, no explanations

KNOWLEDGE:
{batch_content}
    """.strip()

elif args.query_type == "final-analysis":
    prompt = f"""
You are constrained to ONLY the extracted rules below. Do not use external knowledge.

EXTRACTED RULES:
{batch_content}

WORKFLOW TO ANALYZE:
{workflow_content}

INSTRUCTIONS:
1. Check workflow against each relevant rule
2. Count PASS/FAIL conditions
3. Output: APPLICABLE_RULES, SATISFIED_RULES, VIOLATED_RULES, PREDICTION
    """.strip()

# --- Run RAG chain ---
llm = Ollama(model="mistral")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
result = qa.run(prompt)

# --- Save output ---
with open(args.output_file, "w") as f:
    f.write(result)

print("✅ RAG Output:\n", result)
