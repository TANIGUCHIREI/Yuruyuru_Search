import aiohttp
import asyncio
import json
import os
from openai import OpenAI
import nest_asyncio
nest_asyncio.apply()

# Assuming OPENAI_API_KEY is already set in your environment or loaded from a .env file
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

async def fetch_openai_embedding(session, query, attempt=1):
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': 'text-embedding-3-small',
        'input': query,
        'dimensions': 512,
    }

    try:
        async with session.post('https://api.openai.com/v1/embeddings', headers=headers, data=json.dumps(payload)) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception("Non-success status code")
    except Exception as e:
        if attempt <= 5:  # Retry up to 5 times
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            return await fetch_openai_embedding(session, query, attempt + 1)
        else:
            print(f"Failed to fetch embedding for query: {query} after {attempt} attempts due to {e}")
            return None

async def main(queries):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_openai_embedding(session, query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)  # Return exceptions as part of the results
        return results

def create_embedding_queries(queries):
    loop = asyncio.get_event_loop()
    return_results = []
    result = loop.run_until_complete(main(queries))
    for response in result:
        if response:
            query = response["data"][0]["embedding"]
            return_results.append(query)
        else:
            return_results.append(None)  # In case of an error, append None or handle accordingly
    return return_results

if __name__ == "__main__":
    queries = ['query1', 'query2', 'query3', 'query4']
    return_results = create_embedding_queries(queries)
    for result in return_results:
        if result:
            print(result)
        else:
            print("Error or no embedding returned for a query.")