import json
import uuid
from typing import Literal, TypedDict

import chromadb
from pydantic import BaseModel, Field

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from langchain_core.tools.structured import StructuredTool

from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent

client = chromadb.PersistentClient(path="/chromadb")

def save_orders_data(orders_data):
    # Save the orders data to the JSON file
    with open("./retail/orders.json", "w") as file:
        json.dump(orders_data, file)

llm_general = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs=dict(temperature=0.7)  # Slightly higher temperature for more natural conversation
)


members = ["general_conversation_agent", "product_recommendation_agent", "product_details_agent", "product_reviews_agent", "create_order_agent"]

PROMPT_SYSTEM = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["general_conversation_agent", "product_recommendation_agent", "product_details_agent", "product_reviews_agent", "create_order_agent", "FINISH"]

#Supervisor node
def supervisor_node(state: MessagesState) -> Command[Literal["general_conversation_agent", "product_recommendation_agent", "product_details_agent", "product_reviews_agent", "create_order_agent", "__end__"]]:
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
    ] + state["messages"]
    
    #need to return messages to the user when comes from the general conversation agent
    response = llm_general.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto) 

# Add general conversation node
PROMPT_SYSTEM_GENERAL = """
Act as a personal cars consultant. Your name is Juan. You work for a car store. The store sells cars. Handle general conversation, greetings, and basic questions.
Key behaviors:
- Respond warmly to greetings and basic questions about the store.
- Dont use emojis
- Answer always in english
- Keep responses friendly but professional
- Don't make up information about products
"""

def general_conversation_node(state: MessagesState) -> Command[Literal["__end__"]]:
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM_GENERAL},
    ] + state["messages"]
    
    result = llm_general.invoke(messages)
    
    return Command(
        update={
            "messages": [
                HumanMessage(content=result.content, name="general_conversation_agent")
            ]
        },
        goto=END,
    )

def respond_to_user(message: str):
    return f"Respond to the user using the followind data: <data>{message}</data> Dont use a tool call to answer, just respond to the user using the data provided. Answer always in english."




class InterestSchema(BaseModel):
    """Inputs to the recommendation tool."""
    interests: list[str] = Field(
        description="The list of interests of the user to find the best product that matches the interests. Could be type of car, design, usage, etc."
    )

def check_product_recommendation(interests: list[str]):
    try:
        collection = client.get_collection(name="collection_catalog")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_catalog")
    recommendations = []
    data_response = ""
    if interests:
        for interest in interests:
            chroma_docs = collection.query(
                query_texts=[interest],
                n_results=1,
                include=["documents", "metadatas"]
            )
            doc = chroma_docs["documents"][0]
            product = json.loads(doc[0])
            if product["name"] not in recommendations:
                recommendations.append(product)
                data_response += f"Product: {product}\n"
    return llm.invoke(input=respond_to_user(f"The products recommendations are {data_response}")).content

check_product_recommendation_tool = StructuredTool.from_function(
    func=check_product_recommendation,
    name="check_product_recommendation",
    description="List the products recommendations based on the interests of the user",
    args_schema=InterestSchema,
    return_direct=True
)

PROMPT_SYSTEM = """
Act as a personal cars consultant. Your name is Juan. You work for a car store guiding users through the product recommendations.
Respond organizing the data in a friendly way.
If the user asks for the recommendations of a product, call check_product_recommendation_tool to get the recommendations.
if the users give you a list of interests, call check_product_recommendation_tool to get the recommendations.
Answer always in english. Never answer using tags like <user> or <assistant> or anything like that. 
Dont answer about the products with your own knowledge, only answer with the data provided by the tools.
"""
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs=dict(temperature=0),
).bind_tools([check_product_recommendation_tool], tool_choice="auto")

#Check product details agent
product_recommendation_react_agent = create_react_agent(llm, tools=[check_product_recommendation_tool], state_modifier=PROMPT_SYSTEM)

#Check product details node
def product_recommendation_agent_node(state: MessagesState) -> Command[Literal["__end__"]]:
    result = product_recommendation_react_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="product_recommendation_agent")
            ]
        },
        goto=END,
    )
    


class ProductNameSchema(BaseModel):
    """Inputs to the product details tool."""
    product_name: str = Field(
        description="The name of the product to check details"
    )

def check_product_details(product_name: str):
    try:
        collection = client.get_collection(name="collection_catalog")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_catalog")
    if product_name:
        chroma_docs = collection.query(
            query_texts=[product_name],
            n_results=1,
            include=["documents", "metadatas"]
        )
        doc = chroma_docs["documents"][0]
        data_response = ""
        for document in doc:
            data_response += " ".join(document)
            data_response += "\n"   
        return llm.invoke(input=respond_to_user(f"The product details are {data_response}")).content
    return llm.invoke(input=respond_to_user(f"The product with name {product_name} was not found")).content

check_product_details_tool = StructuredTool.from_function(
    func=check_product_details,
    name="check_product_details",
    description="List the details of a product like name, price, description, key features, best for usage, available types",
    args_schema=ProductNameSchema,
    return_direct=True
)

PROMPT_SYSTEM = """
Act as a personal cars consultant. Your name is Juan. You work for a car store guiding users through the product details like name, price, description, best for usage.
Respond organizing the data in a friendly way.
If the user asks for the details of a product, call check_product_details_tool to get the details.
Dont include product ID in the response.
Answer always in english. Never answer using tags like <user> or <assistant> or anything like that. 
Dont answer about the products with your own knowledge, only answer with the data provided by the tools.
"""
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs=dict(temperature=0),
).bind_tools([check_product_details_tool], tool_choice="auto")

#Check product details agent
product_details_react_agent = create_react_agent(llm, tools=[check_product_details_tool], state_modifier=PROMPT_SYSTEM)

#Check product details node
def product_details_agent_node(state: MessagesState) -> Command[Literal["__end__"]]:
    result = product_details_react_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="product_details_agent")
            ]
        },
        goto=END,
    )
    

def check_product_reviews(product_name: str):
    try:
        collection = client.get_collection(name="collection_reviews")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_reviews")
    if product_name:
        chroma_docs = collection.query(
            query_texts=[product_name],
            n_results=1,
            include=["documents", "metadatas"]
        )
        doc = chroma_docs["documents"][0]
        return llm.invoke(input=respond_to_user(f"The product reviews are {doc}")).content
    return llm.invoke(input=respond_to_user(f"The product with name {product_name} was not found")).content

check_product_reviews_tool = StructuredTool.from_function(
    func=check_product_reviews,
    name="check_product_reviews",
    description="List the reviews of a product that contains the user reviewer name, rating, review.",
    args_schema=ProductNameSchema,
    return_direct=True
)    


PROMPT_SYSTEM = """
Act as a personal cars consultant. Your name is Juan. You work for a car store guiding users through the product reviews.
If the user asks for the reviews of a product, call check_product_reviews_tool to get the reviews.
Answer always in english. Never answer using tags like <user> or <assistant> or anything like that. 
Dont answer about the products with your own knowledge, only answer with the data provided by the tools.
"""
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs=dict(temperature=0),
).bind_tools([check_product_reviews_tool], tool_choice="auto")

#Check product reviews agent
product_reviews_react_agent = create_react_agent(llm, tools=[check_product_reviews_tool], state_modifier=PROMPT_SYSTEM)

#Check product reviews node
def product_reviews_agent_node(state: MessagesState) -> Command[Literal["__end__"]]:
    result = product_reviews_react_agent.invoke(state)
    return Command( 
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="product_reviews_agent")
            ]
        },
        goto=END,
    )

   
class OrderSchema(BaseModel):  
    """Inputs to the order tool."""
    email: str = Field(
        description="The email of the user to create an order"
    )
    product_name: str = Field(
        description="The name of the product to create an order"
    )
    quantity: str = Field(
        description="The quantity of the product to create an order"
    )
    
def get_product_price(product_name: str):
    try:
        collection = client.get_collection(name="collection_catalog")
    except Exception as e:  # ChromaDB raises Error if collection doesn't exist
        collection = client.create_collection(name="collection_catalog")
    if product_name:
        chroma_docs = collection.query(
            query_texts=[product_name],
            n_results=1,
            include=["documents", "metadatas"]
        )
        return chroma_docs["documents"][0]
    return None

def create_order(email: str, product_name: str, quantity: str):
    if email and product_name and quantity:
        order_id = str(uuid.uuid4())
        product = get_product_price(product_name)
        if product:
            product_price = json.loads(product[0])["price"]
            total = float(product_price) * int(quantity)
            orders_data = {"order_id": order_id, "email": email, "product": product_name, "quantity": quantity, "total": total}
            save_orders_data(orders_data)
            return llm.invoke(input=respond_to_user(f"The order has been created for the user {email} with the product {product_name} and the total price is {total}")).content
        return llm.invoke(input=respond_to_user(f"The order has not been created because the product {product_name} was not found")).content
    return llm.invoke(input=respond_to_user(f"The order has not been created because the user {email} or the product {product_name} or the quantity {quantity} was not provided")).content

create_order_tool = StructuredTool.from_function(
    func=create_order,
    name="create_order",
    description="Create an order when user provides an email, product name, and quantity.",
    args_schema=OrderSchema,
    return_direct=True
)

PROMPT_SYSTEM = """
Act as a personal cars consultant. Your name is Juan. You work for a car store guiding users through the order creation.
If the user asks to create an order or to buy a car, You should first ask for the email, product name, and quantity if they were not provided. 
If the user provides the email, product name, and quantity, then call create_order_agent with the email, product name, and quantity provided by the user.
Answer always in english. Never answer using tags like <user> or <assistant> or anything like that. 
Dont answer about the products with your own knowledge, only answer with the data provided by the tools.
"""
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs=dict(temperature=0),
).bind_tools([create_order_tool], tool_choice="auto")

#Check product reviews agent
create_order_react_agent = create_react_agent(llm, tools=[create_order_tool], state_modifier=PROMPT_SYSTEM)

#Create order node
def create_order_agent_node(state: MessagesState) -> Command[Literal["__end__"]]:
    result = create_order_react_agent.invoke(state)
    return Command( 
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="create_order_agent")
            ]
        },
        goto=END,
    )





builder = StateGraph(MessagesState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("general_conversation_agent", general_conversation_node)
builder.add_node("product_recommendation_agent", product_recommendation_agent_node)
builder.add_node("product_details_agent", product_details_agent_node)
builder.add_node("product_reviews_agent", product_reviews_agent_node)
builder.add_node("create_order_agent", create_order_agent_node)
graph_builder = builder.compile()