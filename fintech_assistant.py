from llm_utils import call_llm
import uuid
import chromadb
import PyPDF2

client = chromadb.PersistentClient(path="/chromadb")
#client.delete_collection(name="collection_fintech")

try:
    collection = client.get_collection(name="collection_fintech")
except Exception as e:  # ChromaDB raises Error if collection doesn't exist
    collection = client.create_collection(name="collection_fintech")


# Load the PDF file
file_path = "./fintech_assistant.pdf"
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
size_chunk = 256
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
    print("--------------------------------","batch",index,"of",number_chunks)

# Define the input prompt of the user   
input_prompt = "Como puedo cambiar mi contraseña?"

# Generate a new question based on the input prompt
query_expansion = f"Actua como un cliente recurrente de un banco y reescribe la pregunta {input_prompt} en un formato que sea facil de entender para un asistente de un banco. No devuelvas nada mas."
new_question = call_llm(query_expansion)
print(new_question)
# Retrieve the documents from the collection based on the questions

results = collection.query(
    query_texts=new_question,
    n_results=2,
    include=['documents']
)
retrieved_documents = results['documents'][0]
data_response = ""
for document in retrieved_documents:
    data_response += " ".join(document)
    data_response += "\n"   


print("Información relevante:")
print(data_response)

# Check if the information is relevant to the question
query_check = f"Verifica que esta informacion {data_response} sea relevante para la pregunta {input_prompt}. Retorna un booleano True o False. No devuelvas nada mas."

response_check = call_llm(query_check)

# If the information is relevant, generate a response using the RAG model
if response_check:
    rag_response = f"Actua como un asistente de un banco y responde la pregunta {input_prompt} con la informacion relevante contenida en {data_response}"
    response_rag = call_llm(rag_response)
    print("Respuesta generada por el modelo RAG:")
    print(response_rag)
# If the information is not relevant, pass to a human advisor
else:
    print("Pasamos a un asesor humano")