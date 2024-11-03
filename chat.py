import streamlit as st
from proptech_agent import graph_builder    
from langchain_core.messages import HumanMessage
import uuid

thread_id = str(uuid.uuid4())
st.title("💬 ChatBot")

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