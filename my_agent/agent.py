from google.adk.agents.llm_agent import Agent
from my_agent.tools import get_gvb_disruptions, get_public_transport_route

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
    tools=[get_gvb_disruptions, get_public_transport_route]
)
