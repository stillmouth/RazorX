import os
import requests

def generate_sql_via_api(question, schema):
    if not question.strip():  # If the question is empty or just whitespace
        return ["No query found."]

    # Set the endpoint and headers
    url = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
    api_key = os.getenv('GROQ_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Modify prompt to request multiple queries
    prompt = (
        f"Given the database schema:\n{schema}\n\n"
        f"Question: {question}\n\n"
        f"Generate all RELEVANT SQLite3 (SQL) queries needed to extract useful insights for reports and trends. "
        f"Ensure they are diverse and meaningful. "
        f"Return them as a numbered list with each query on a new line. "
        f"Do not include explanations, just the queries."
    )

    # Prepare the payload for the API request
    payload = {
        "model": "llama-3.3-70b-versatile",  # Adjust the model as needed
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            raw_queries = result['choices'][0]['message']['content'].strip()

            # Extract SQL queries from numbered list format
            queries = [query.split('. ', 1)[-1].strip() for query in raw_queries.split("\n") if query.strip()]
            return queries
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return ["Error generating SQL queries."]
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return ["Error generating SQL queries."]
