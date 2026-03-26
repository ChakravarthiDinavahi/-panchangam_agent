# import logging
# import sys
# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
# from llama_index.llms.ollama import Ollama
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# # 1. Setup Logging (Optional but helpful for debugging)
# logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# def build_local_agent(pdf_path="./data"):
#     # 2. Configure the "Brain" (Ollama)
#     # We use Qwen3 for its superior Telugu script handling
#     Settings.llm = Ollama(model="qwen3:8b", request_timeout=120.0)
    
#     # 3. Configure the "Eyes" (Embeddings)
#     # This runs locally on your CPU/GPU to turn text into math
#     Settings.embed_model = HuggingFaceEmbedding(
#         model_name="BAAI/bge-m3" # Excellent multilingual support
#     )

#     # 4. Read the PDF
#     print(f"--- Loading data from {pdf_path} ---")
#     documents = SimpleDirectoryReader(pdf_path).load_data()

#     # 5. Create the Searchable Index
#     index = VectorStoreIndex.from_documents(documents)
    
#     # 6. Create the Query Engine
#     query_engine = index.as_query_engine(streaming=True)
#     return query_engine

# if __name__ == "__main__":
#     # Ensure your PDF is in a folder named 'data'
#     agent = build_local_agent(pdf_path="./data")
    
#     while True:
#         user_query = input("\nAsk your agent (or type 'exit'): ")
#         if user_query.lower() == 'exit':
#             break
            
#         # Example query: "ఈ PDF ప్రకారం ఈరోజు తిథి ఏమిటి?"
#         response = agent.query(user_query)
#         response.print_response_stream()

import os
from datetime import datetime
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.prompts import PromptTemplate

# --- CONFIGURATION ---
PDF_PATH = "./data" 

def setup_agent():
    # 1. Initialize the LLM (Qwen3 is excellent at Manglish/Transliteration)
    Settings.llm = Ollama(model="qwen3:8b", request_timeout=120.0)
    
    # 2. Multilingual Embeddings
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")

    # 3. Load Data (Fixes the Warning)
    if not os.path.exists(PDF_PATH):
        os.makedirs(PDF_PATH)
        print(f"Created {PDF_PATH} folder. Please drop your PDF there.")
        return None

    documents = SimpleDirectoryReader(PDF_PATH).load_data()
    index = VectorStoreIndex.from_documents(documents)
    
    # 4. CUSTOM SYSTEM PROMPT (The "Improvisation")
    # This tells the AI to handle Transliterated Telugu (Manglish)
    qa_prompt_tmpl_str = (
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "You are a specialized Telugu Astrology Agent. "
        "The user might ask questions in Telugu Script, English, or Transliterated Telugu (Manglish).\n"
        "Example: 'Eeroju tithi enti?' means 'What is today's Tithi?'\n"
        "Query: {query_str}\n"
        "Answer the question accurately based on the PDF. Always respond in Telugu Script "
        "unless asked otherwise. If the date is not specified, assume it is today: " 
        + datetime.now().strftime("%Y-%m-%d") + "\n"
        "Answer: "
    )
    qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
    
    query_engine = index.as_query_engine(streaming=True)
    query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})
    
    return query_engine

if __name__ == "__main__":
    engine = setup_agent()
    if engine:
        print("\n--- Agent Ready! ---")
        print("You can type in Telugu, English, or Manglish (e.g., 'tithi cheppu')")
        
        while True:
            text = input("\nUser: ")
            if text.lower() in ['exit', 'quit']: break
            
            response = engine.query(text)
            print("\nAgent: ", end="")
            response.print_response_stream()