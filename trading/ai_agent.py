from openai import OpenAI
from dotenv import load_dotenv
import os

# Import API key
load_dotenv(dotenv_path="auth.env")
agent_key = os.getenv("openai_key")
client = OpenAI(api_key=agent_key)

prompt = """
Forget all your previous instructions. Given a webpage link, you will only response, if any, with the number of ⚡ present. 
You will find the value in the right tab containing all the pool data in a button called \"⚡ Boost \". This button is placed above the user reactions. 
Please, return only the value requested. If the value is not available, just return \"0\".
"""

url = "https://dexscreener.com/solana/{}"

def get_boosts(address):
    response = client.responses.create(

        model="gpt-4o", # update with a newer model here
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": url.format(address)}
            ],

        tools=[
            {
            "type": "web_search_preview",
            "user_location": {"type": "approximate"},
            "search_context_size": "medium"
            }
        ],

        tool_choice={"type": "web_search_preview"},
        temperature=1,
        max_output_tokens=2048,
        top_p=1,
        )
    boost = response.output_text.strip()
    return boost