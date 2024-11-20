import uuid
import PyPDF2
import chromadb
import streamlit as st
from llm_utils import call_llm

client = chromadb.PersistentClient(path="/chromadb")



st.header("Credit Document Analysis")

# Button to delete collection
if st.button('Delete Credit Document Data'):
    client.delete_collection(name="collection_credit_document")

# Button to load data
if st.button('Load Credit Document Data'):
    try:
        collection = client.get_collection(name="collection_credit_document")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_credit_document")

    # Load the PDF file
    file_path = "./fintech/credit_document.pdf"
    pdf_reader = PyPDF2.PdfReader(open(file_path, "rb"))

    # Extract the text from the PDF
    pdf_text = ""
    for page in range(len(pdf_reader.pages)):
        pdf_text += pdf_reader.pages[page].extract_text()
        
    # Function to preprocess the text to normalize encoding
    def preprocess_text(text):
        # Convert to UTF-8 and remove non-printable characters
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    # Preprocess the text to normalize encoding
    pdf_text = preprocess_text(pdf_text)
    # Define the size of the chunks and the number of chunks
    size_chunk = 1024
    number_chunks = len(pdf_text)//size_chunk

    # Add the chunks to the collection
    for index in range(number_chunks):
        if (index+1)*size_chunk > len(pdf_text):
            text_chunk = pdf_text[index*size_chunk:len(pdf_text)-1]
        else:
            text_chunk = pdf_text[index*size_chunk:(index+1)*size_chunk]
        collection.add(
            documents=[text_chunk],
            ids=[str(uuid.uuid4())]
        )
        print("--------------------------------","batch",index,"of",number_chunks-1)

def vector_search(query):
    collection = client.get_collection(name="collection_credit_document")
    results = collection.query(
        query_texts=query,
        n_results=3,
        include=['documents','distances']
    )
    st.title("Results")
    st.write(results)
    return results,results['documents'][0], results['distances'][0]

def query_expansion(query):
    PROMPT_QUERY_EXPANSION = f"""
    Act as a financial advisor. 
    A person will sign a credit document. 
    You need to obtain more information about the credit document to be sure that is the best option for the person. 
    You are given this query:
    {query}
    Rewrite the query to be more specific and very relevant to search in the credit document. 
    Use synonyms to expand the query.
    """
    return call_llm(PROMPT_QUERY_EXPANSION)

def retrieval_augmentation(query,retrieved_documents):
    PROMPT_RETRIEVAL_AUGMENTATION = f"""
    Act as a financial advisor. 
    A person will sign a credit document. 
    You need to obtain more information about the credit document to be sure that is the best option for the person. 
    You are given this query:
    {query}
    You also have these documents that are relevant to the query:
    {retrieved_documents}
    Analyze the query and respond to the person using documents that are relevant to the query.
    Don not user you own knowledge, only use the documents to answer the question.
    Answer in one phrase. Be very specific. Be concise.
    If you don't know the answer, say these is not in the documents. Dont comment about the documents.
    Answer in spanish.
    """
    return call_llm(PROMPT_RETRIEVAL_AUGMENTATION)

# st input to ask for a comment
input_question = st.text_input("Ask a question about the credit document")

# if comment is not empty, find in collection
if input_question:
    query_expanded = query_expansion(input_question)
    results,retrieved_documents,distances = vector_search(query_expanded)
    
    st.title("Results distances")
    st.write(distances)
    st.title("Results documents")
    st.write(retrieved_documents)
    documents_response = ""
    for document in retrieved_documents:
        documents_response += " ".join(document)
        documents_response += "\n" 
    st.title("Documents response")
    st.write(documents_response)
    
    retrieval_augmentation_response = retrieval_augmentation(input_question,documents_response)
    st.title("Retrieval augmentation response")
    st.write(retrieval_augmentation_response)

CREDIT_QUERIES = {
    "interest_rate": "Tasa de interes del credito",
    "interest_type": "Tipo de tasa de interes",
    "amount": "Monto, cupo o limite de credito",
    "payment_term": "Plazo maximo de pago o cuotas maximas de pago",
    "grace_period": "Plazo o tiempo maximo de pago sin interes",
    "cash_advance": "Adelantos de dinero",
    "fraud_prevention": "Medidas del banco para evitar fraudes",
    "payment_methods": "Metodos o formas de pago",
    "refinancing": "Refinanciamiento del credito",
    "insurance": "Seguro en caso de muerte, incapacidad o desempleo",
    "termination": "Terminacion, cancelacion o clausura del credito"
}

if st.button('Principal Components Analysis'):
    for key in CREDIT_QUERIES.keys():
        query_expanded = query_expansion(CREDIT_QUERIES[key])
        results,retrieved_documents,distances = vector_search(query_expanded)
        retrieval_augmentation_response = retrieval_augmentation(CREDIT_QUERIES[key],retrieved_documents)
        st.title(key)
        st.write(retrieval_augmentation_response)