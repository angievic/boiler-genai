import streamlit as st
import json
import uuid

import chromadb

from langchain_core.messages import HumanMessage
from retail.multiagent import graph_builder

client = chromadb.PersistentClient(path="/chromadb")

if st.button("Save catalog"):
    try:
        collection = client.get_collection(name="collection_catalog")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_catalog")
    # Load the PDF file
    file_path = "./retail/catalog.json"
    with open(file_path, "r") as file:
        catalog_data = json.load(file)
    
    # Add each product as a separate document
    for i, product in enumerate(catalog_data["products"]):
        collection.add(
            documents=[json.dumps(product)],
            ids=[str(uuid.uuid4())],
            metadatas=[{"product_id": product["product_id"]}]
        )
        print(f"Added product {i+1} of {len(catalog_data)}")
        
if st.button("Save reviews"):
    try:
        collection = client.get_collection(name="collection_reviews")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_reviews")

    file_path = "./retail/reviews.json"
    with open(file_path, "r") as file:
        reviews_data = json.load(file)
        
    # Add each review as a separate document
    for i, review in enumerate(reviews_data["reviews"]):
        collection.add(
            documents=[json.dumps(review)],
            ids=[str(uuid.uuid4())],
            metadatas=[{"product_id": review["product_id"]}]
        )
        print(f"Added review {i+1} of {len(reviews_data)}")
        
        
st.title("💬 ChatBot")

thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
    
# Medical assistant
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = graph_builder.invoke(
        {"messages": [HumanMessage(content=prompt)]+st.session_state.messages},
        config={"configurable": {"thread_id": thread_id}}
    )
    msg = response["messages"][-1].content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

        


