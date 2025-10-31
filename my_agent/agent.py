from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from my_agent.tools import get_gvb_disruptions, get_public_transport_route, get_weather_forecast
from google.adk.tools import google_search

Agent_Search = Agent(
    model='gemini-2.0-flash-exp',
    name='SearchAgent',
    instruction="""
    You're a spealist in Google Search
    """,
    tools=[google_search]
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions. When providing public transport routes, also check for and include any disruptions (e.g., lift or escalator outages) at the origin and destination stations, and provide weather recommendations for the destination.',
    instruction='Answer user questions to the best of your knowledge. When providing public transport routes, also check for and include any disruptions (e.g., lift or escalator outages) at the origin and destination stations. When asked for weather, use the get_weather_forecast tool, ensuring to provide literal latitude, longitude, and a Unix timestamp for the desired time.',
    tools=[get_gvb_disruptions, get_public_transport_route, get_weather_forecast,  AgentTool(agent=Agent_Search)]
)
