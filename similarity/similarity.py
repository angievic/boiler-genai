import chromadb
from typing import List
import streamlit as st
from llm_utils import call_llm
import json

client = chromadb.PersistentClient(path="/chromadb")

table_a = [
    {"id": "1", "text": "angie z"},
    {"id": "2", "text": "juliana Paola"},
    {"id": "3", "text": "a"},
]
table_b = [
    {"id": "4", "text": "Angie Z"},
    {"id": "5", "text": "Juliana paol"},
    {"id": "6", "text": "angiie"},
    {"id": "7", "text": "juuliana"}
]

if st.button("Save data tables"):
    try:
        collection = client.get_collection(name="similarity_collection")
    except Exception as e:
        collection = client.create_collection(name="similarity_collection")

    for table in table_a:
        collection.add(documents=[table["text"]], ids=[table["id"]])

    for table in table_b:
        collection.add(documents=[table["text"]], ids=[table["id"]])
    
def similarity_search(query: str, collection_name: str, k: int = 5, threshold: float = 0.85) -> List[str]:
    collection = client.get_collection(name=collection_name)
    results = collection.query(query_texts=[query], n_results=k, include=["documents", "distances"])
    final_results = []
    for index, result in enumerate(results["distances"][0]):
        if result <= threshold:
            final_results.append({"id": results["ids"][0][index], "text": results["documents"][0][index]})
    return final_results

query = st.text_input("query")
if query:
    results = similarity_search(query, "similarity_collection", k=5, threshold=0.85)
    if st.button("Check similarity with LLM"):
        st.write(results)
        response = call_llm(f"""
            You are a helpful assistant that can search for similar items in a database.
            You are given a query and a list of similar items.
            You need to return the most similar item to the query.
            Query: {query}
            Similar items: {results}
            Return as a json with the following format:
            {{
                "query": "{query}",
                "similar_items": ["item1", "item2", "item3"]
            }}
            Return only the json, no other text or comments.
        """)
        final_result = json.loads(response)
        st.write(final_result)

