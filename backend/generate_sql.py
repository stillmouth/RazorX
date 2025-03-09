import os
import requests

def generate_sql_via_api(question, schema):
    if not question.strip():  # If the question is empty or just whitespace
        return "No query found."

    # Set the endpoint and headers
    url = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
    api_key = os.getenv('GROQ_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Prepare the data for the API request
    payload = {
        "model": "llama-3.3-70b-versatile",  # Adjust the model as needed
        "messages": [{
            "role": "user",
            "content": f"Given the schema:\n{schema}\n\nQuestion: {question}\n\nGenerate ONLY the SQLite3 (SQL) query. IF YOU ARE FORCED TO MAKE ASSUMPTIONS, return ERROR"
        }]
    }

    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            sql_query = result['choices'][0]['message']['content'].strip()

            # Clean the SQL query by removing triple backticks and 'sql' keyword
            cleaned_sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            return cleaned_sql_query
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return "Error generating SQL query."
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return "Error generating SQL query."