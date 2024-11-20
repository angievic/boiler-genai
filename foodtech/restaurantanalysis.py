import os
import uuid
import pandas as pd
import chromadb
import streamlit as st
import json
from llm_utils import call_llm

client = chromadb.PersistentClient(path="/chromadb")

def analysis_comment(comment):
    PROMPT_ANALYSIS = """
    Analyze the following user comment for a restaurant:
    {comment}   

    Your task is to extract the following information:
    - general_satisfied (true/false)\
    - like_food (true/false)\
    - like_service (true/false)\
    - like_ambiance (true/false)\
    - like_price (true/false)\
    - like_location (true/false)\

    Return the information in the following formatJSON example:
    {{
        "general_satisfied": true,
        "like_food": true,
        "like_service": true,
        "like_ambiance": false,
        "like_price": true,
        "like_location": false
    }}
    Do not include any other text than the JSON.
    """
    return json.loads(call_llm(PROMPT_ANALYSIS.format(comment=comment)))

st.header("Restaurant Analysis")


# Button to delete collection
if st.button('Delete Restaurant Data'):
    client.delete_collection(name="collection_restaurant")
    

# Button to load data
if st.button('Load Restaurant Data'):
    try:
        collection = client.get_collection(name="collection_restaurant")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_restaurant")

    df = pd.read_csv('./foodtech/restaurantdata.csv')
    # where column head is comment
    data = df[df.columns[9]].to_list()
    st.write(data)
    for item in data:
        # save in collection each comment
        collection.add(
            documents=[item],
            ids=[str(uuid.uuid4())]
        )
    if not os.path.exists('./foodtech/data_response.json'):
        data_response = []
        for item in data:
            analysis = analysis_comment(item)
            data_response.append(analysis)
        # save data_response in a file
        with open('./foodtech/data_response.json', 'w') as f:
            json.dump(data_response, f)

# st input to ask for a comment
ask_comment = st.text_input("Find data in comments")

# if comment is not empty, find in collection
if ask_comment:
    collection = client.get_collection(name="collection_restaurant")
    results = collection.query(
        query_texts=ask_comment,
        n_results=5,
        include=['documents']
    )
    retrieved_documents = results['documents'][0]
    data_response = []
    for document in retrieved_documents:
        data_response.append(" ".join(document))
    st.write(data_response)
    
    
# button to visualize data_response
if st.button('Visualize Data Response'):
    with open('./foodtech/data_response.json', 'r') as f:
        data_response = json.load(f)
    total_responses = len(data_response)
    total_general_satisfied = 0
    total_like_food = 0
    total_like_service = 0
    total_like_ambiance = 0
    total_like_price = 0
    total_like_location = 0
    for analysis in data_response:  
        # calculate the numbers of general satisfied
        total_general_satisfied += analysis['general_satisfied']
        total_like_food += analysis['like_food']
        total_like_service += analysis['like_service']
        total_like_ambiance += analysis['like_ambiance']
        total_like_price += analysis['like_price']
        total_like_location += analysis['like_location']
    # Calculate percentages
    percentages = {
        'General Satisfaction': (total_general_satisfied / total_responses) * 100,
        'Food': (total_like_food / total_responses) * 100,
        'Service': (total_like_service / total_responses) * 100,
        'Ambiance': (total_like_ambiance / total_responses) * 100,
        'Price': (total_like_price / total_responses) * 100,
        'Location': (total_like_location / total_responses) * 100
    }
    
    st.header("Data Visualization")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("General Satisfaction", f"{percentages['General Satisfaction']:.1f}%")
        st.metric("Food Rating", f"{percentages['Food']:.1f}%")
    with col2:
        st.metric("Service Rating", f"{percentages['Service']:.1f}%")
        st.metric("Ambiance Rating", f"{percentages['Ambiance']:.1f}%")
    with col3:
        st.metric("Price Rating", f"{percentages['Price']:.1f}%")
        st.metric("Location Rating", f"{percentages['Location']:.1f}%")
    
    # Bar Chart
    st.subheader("Category Ratings Comparison")
    st.bar_chart(percentages)
    
    # Line Chart
    st.subheader("Ratings Distribution")
    st.line_chart(percentages)
    
    # Area Chart
    st.subheader("Ratings Overview")
    st.area_chart(percentages)
    
    # Display raw numbers
    st.subheader("Raw Numbers")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Total Responses:", total_responses)
        st.write("Generally Satisfied:", total_general_satisfied)
        st.write("Like Food:", total_like_food)
        st.write("Like Service:", total_like_service)
    with col2:
        st.write("Like Ambiance:", total_like_ambiance)
        st.write("Like Price:", total_like_price)
        st.write("Like Location:", total_like_location)
    
    # Optional: Add a download button for the data
    st.download_button(
        label="Download Analysis Data",
        data=str(percentages),
        file_name="restaurant_analysis.txt",
        mime="text/plain"
    )