import json
import os
import random
import matplotlib.pyplot as plt
import seaborn as sns
from google import genai
import pandas as pd
# Set up Google API client
API_KEY = os.environ.get("GOOGLE_GRAPH_API_KEY")  # Fetch from environment variables
client = genai.Client(api_key=API_KEY)

# Load SQL results from file
with open("sql_results.json", "r") as file:
    sql_results = json.load(file)

# Ensure charts folder exists
os.makedirs("charts", exist_ok=True)

# Prepare a sample (max 12 rows per query) for the API prompt
query_samples = []
for result in sql_results:
    query = result["query"]
    rows = result["rows"]
    sample_rows = random.sample(rows, min(12, len(rows)))
    query_samples.append({"query": query, "sample": sample_rows})

# Construct the prompt with all queries and their sample data in one go
prompt = """Write a Python script to visualize the following SQL query results:

"""
for qs in query_samples:
    prompt += f"Query: {qs['query']}\nSample Data: {qs['sample']}\n\n"

prompt += """For each query, generate an appropriate graph using matplotlib or seaborn and save it as a PNG file in the 'charts' folder.
Assume matplotlib and seaborn are already imported, and do not include any import statements.
Return only valid Python code without explanations, comments, or markdown formatting. Be creative in your graphs.
You must diversify the amount of graphs whenever appropriate. Use different kind of bar charts, pie charts, pairplots, lineplots, histograms,
scatter plots, box plots, heatmaps wherever appropriate but ensure you use different kind of charts and not just bar plots.
The function name must be "visualize_query(query_index, query_data, description="")"
Ensure all the column names are proper. Make your plots colorful. Add Legends. 
Ensure the titles are appropriate and customised well for the query. 
Use appropriate graphs for results with only one column.
"""

# Send the prompt in a single API call to generate the visualization code
response = client.models.generate_content(
    model="gemini-2.0-flash-thinking-exp-01-21", contents=prompt
)
generated_code = response.text

# Remove markdown formatting if present
if generated_code.startswith("```python"):
    generated_code = generated_code[9:]
if generated_code.endswith("```"):
    generated_code = generated_code[:-3]

print("Generated Code:\n", generated_code)  # Debugging step

# Prepare the full dataset for execution; store the original list-of-dictionaries.
exec_env = {"os": os, "plt": plt, "sns": sns, "data_sets": {}}
for result in sql_results:
    query = result["query"]
    rows = result["rows"]
    exec_env["data_sets"][query] = rows  # Use the original list-of-dictionaries

# Execute the generated code. This code should define a function 'visualize_query'
exec(generated_code, exec_env)

# Call the visualization function on each full dataset.
if "visualize_query" in exec_env:
    for i, (query_text, full_data) in enumerate(exec_env["data_sets"].items(), start=1):
        query_name = f"query{i}"
        try:
            exec_env["visualize_query"](i, full_data)
            print(f"Graph for query '{query_text}' saved as charts/{query_name}.png")
        except Exception as e:
            print(f"Error generating graph for query '{query_text}': {e}")
else:
    print("No visualization function found in generated code.")

print("Graphs saved in charts folder.")
