from pydantic import BaseModel, Field
from langchain_core.tools.structured import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent

properties_data = {         
    "123":"available",
    "456": "unavailable",
    "789": "available"
}

property_calendar_data = {
    "123": ["2024-10-30 10:00", "2024-10-31 11:00"],
    "456": ["2024-10-30 14:00", "2024-10-31 15:00", "2024-11-01 16:00"],
    "789": ["2024-10-30 10:00", "2024-10-31 11:00"]
}

property_visit_data = {
    "123": ["2024-10-30 10:00", "2024-10-31 11:00"],
    "456": ["2024-10-30 14:00", "2024-10-31 15:00", "2024-11-01 16:00"],
    "789": ["2024-10-30 10:00", "2024-10-31 11:00"]
}

property_details_data = {
    "123": {"address": "Usaquen", "city": "Bogota", "state": "Colombia", "zip": "12345", "owner": "John Doe", "price": "$1000", "description": "A nice house with a garden", "amenities": ["wifi", "tv", "pool", "parking"]},
    "456": {"address": "Mapocho", "city": "Santiago", "state": "Chile", "zip": "67890", "owner": "Juan Perez", "price": "$1500", "description": "A nice apartment with a view to the park", "amenities": ["wifi", "tv","gym"]},
    "789": {"address": "Riomar", "city": "Barranquilla", "state": "Colombia", "zip": "84736", "owner": "Maria Gomez", "price": "$1200", "description": "A nice apartment with a pool", "amenities": ["wifi", "tv", "pool"]}
}

class PropertyIdSchema(BaseModel):
    """Inputs to the property availability, calendar and details tools."""
    id: str = Field(
        description="The id of the property to check availability, calendar or details"
    )
    
class DateTimeSchema(BaseModel):  
    """Inputs to the property visit tool."""
    id: str = Field(
        description="The id of the property to set a visit"
    )
    date_time: str = Field(
        description="The date and time to set a visit"
    )
    
def respond_to_user(message: str):
    return f"Respond to the user using the followind data: <data>{message}</data> Dont use a tool call to answer, just respond to the user using the data provided. Answer always in spanish."

# Define the tools for the agent to use     
def check_property_availability(id:str):
    """Check if a property is available.
    """
    result = check_property_availability_aux(id)
    return llm.invoke(input=result).content
    

def check_property_availability_aux(property_id: str):
    if property_id in properties_data:
        return respond_to_user(f"The property with id {property_id} is {properties_data[property_id]}")
    return respond_to_user(f"The property with id {property_id} was not found")


def check_property_calendar(id:str):
    """Check the calendar of a property.
    """
    result = check_property_calendar_aux(id)
    return llm.invoke(input=result).content
    
def check_property_calendar_aux(property_id: str):
    if property_id in property_calendar_data:
        return respond_to_user(f"The property with id {property_id} has the following calendar for a visit: {property_calendar_data[property_id]}") 
    return respond_to_user(f"The property with id {property_id} was not found")


def set_property_visit(id:str, date_time:str):
    """Set a visit to a property.
    """
    result = set_property_visit_aux(id,date_time)
    return llm.invoke(input=result).content

def set_property_visit_aux(property_id: str, date_time: str):
    if property_id in property_visit_data:
        if date_time in property_calendar_data[property_id]:
            property_visit_data[property_id].append(date_time)
            return respond_to_user(f"The visit to the property with id {property_id} has been set for {date_time}")
        else:
            return respond_to_user(f"The date and time {date_time} is not available for the property with id {property_id}. Do you want that i check the calendar for available dates and times?")
    else:
        return respond_to_user(f"The property with id {property_id} was not found")


def get_property_details(id:str):
    """Get the details of a property.
    """
    result = get_property_details_aux(id)
    return llm.invoke(input=result).content

def get_property_details_aux(property_id: str):
    if property_id in property_details_data:
        return respond_to_user(f"The property with id {property_id} has the following details: {property_details_data[property_id]}")
    else:
        return respond_to_user(f"The property with id {property_id} was not found")

# Convert each function into a structured tool
check_property_availability_tool = StructuredTool.from_function(
    func=check_property_availability,
    name="check_property_availability",
    description="Check if a property is available or unavailable for rent.",
    args_schema=PropertyIdSchema,
    return_direct=True
)
check_property_calendar_tool = StructuredTool.from_function(
    func=check_property_calendar,
    name="check_property_calendar",
    description="Check the calendar available dates and times for a visit to a property. Give information needed to schedule a visit.",
    args_schema=PropertyIdSchema,
    return_direct=True
)               
set_property_visit_tool = StructuredTool.from_function(
    func=set_property_visit,
    name="set_property_visit",
    description="Schedule a visit to a property when user provides a date and time.",
    args_schema=DateTimeSchema,
    return_direct=True
)
get_property_details_tool = StructuredTool.from_function(
    func=get_property_details,
    name="get_property_details",
    description="Get the details of a property like address, owner, price, description and amenities.",
    args_schema=PropertyIdSchema,
    return_direct=True
)
TOOLS = [check_property_availability_tool, check_property_calendar_tool, set_property_visit_tool, get_property_details_tool]

llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs=dict(temperature=0),
).bind_tools(TOOLS, tool_choice="auto")

PROMPT_SYSTEM = """
Act as a helpful assistant for property management that will guide leads through the property details, availability, calendar and visits schedule.
Store the property_id in the state. Dont ask for the property_id if it was already stored. 
Answer always in spanish. Never answer using tags like <user> or <assistant> or anything like that. 
Dont answer about the properties with your own knowledge, only answer with the data provided by the tools.

Conditions to call the tools:
- Call the tools only if you dont have the information to answer the user.
- Call the tools with the exact parameters needed to answer the user.
- When users ask about a property, first check if the property is available for rent. If the property is not available, inform the user and dont call any tool.
- If the property is available, call check_property_calendar_tool to get the available dates and times for a visit.
- Call set_property_visit_tool with the date and time provided by the user. If the date and time was not provided, dont call this tool instead call check_property_calendar_tool.
- Dont call set_property_visit_tool if the property it not available.
"""

#tool_node = ToolNode(name="tools", tools=TOOLS, messages_key="messages")
graph_builder = create_react_agent(llm, tools=TOOLS, state_modifier=PROMPT_SYSTEM,checkpointer=MemorySaver())