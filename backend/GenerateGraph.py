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

prompt += """For each query, generate an appropriate graph using matplotlib or seaborn and save it as a PNG file in the 'charts' folder that is in the same directory.
Assume matplotlib and seaborn are already imported, and do not include any import statements.
Return only valid Python code without explanations, comments, or markdown formatting. Be creative in your graphs.
You must diversify the amount of graphs whenever appropriate. Use different kind of bar charts, pie charts, pairplots, lineplots, histograms,
scatter plots, box plots, heatmaps wherever appropriate but ensure you use different kind of charts and not just bar plots.
The function name must be "visualize_query(query_index, query_data, description="")"
Ensure all the column names are proper. Make your plots colorful. Add Legends. We have limited those results containing a lot of rows to maximum 12 rows.
Hence, ensure your code for such queries fit the entire dataset and not just the 12 rows displayed to you. However, everything else you can display properly as is. 
Ensure the titles are appropriate and customised well for the query. 
Use appropriate graphs for results with only one column.
The filename must be exactly 'queryi.png' where i is the serial number starting from 1.
Do not add any prefixes like 'chart_', 'graph_', or any other text.
Save the file using: plt.savefig(description, bbox_inches="tight").
If the query involves dates, years, or time-based data, convert them into a **numeric** or **datetime** format before plotting.
If the x-axis contains years or dates, **convert them to integers or datetime format** to avoid string-based errors.
"""

# Send the prompt in a single API call to generate the visualization code
response = client.models.generate_content(
    model="gemini-2.0-flash-thinking-exp-01-21", contents=prompt
)

descriptionprompt = """For the following queries with their results (limited to max 12 if there are a lot of rows per query):\n"""

for i, qs in enumerate(query_samples, start=1):
    descriptionprompt += f"Query {i}: {qs['query']}\nSample Data: {qs['sample']}\n\n"

descriptionprompt += """Generate an analytical description (about 2 sentences) for each query and its results.
Return it in the format: 'queryi:descriptioni' where i is the serial number of each query starting from 1.
Do note, that results with a lot of rows are limited to maximum of 12 so ensure you do not consider only those results displayed
to you, in such queries only.
"""

descriptionresponse = client.models.generate_content(
    model='gemini-2.0-flash-thinking-exp-01-21', contents=descriptionprompt
).text

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
        query_filename = f"charts/query{i}.png"  # Ensure it's query1.png, query2.png, etc.
        try:
            # Pass the filename to the visualize_query function
            exec_env["visualize_query"](i, full_data, description=query_filename)
            print(f"Graph for query '{query_text}' saved as {query_filename}")
        except Exception as e:
            print(f"Error generating graph for query '{query_text}': {e}")
else:
    print("No visualization function found in generated code.")

print("Graphs saved in charts folder.")
print("Descriptions: ", descriptionresponse)
#-----------------------------------------------------------------------------------------------

# PDF Report Generator:
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage
import os

# Parse descriptions from the description response
description_lines = descriptionresponse.strip().split("\n")
descriptions = {}
for line in description_lines:
    if line.startswith("query"):
        query_id, description = line.split(":", 1)
        descriptions[query_id.strip()] = description.strip()

# Extract SQL queries from query_samples
sql_queries = {f"query{i+1}": qs["query"] for i, qs in enumerate(query_samples)}

# Create PDF document
pdf_filename = "query_report.pdf"
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    title="RazorX Generated Report",
    author="RazorX",
    subject="SQL Query Visualizations",
)

# Define styles
styles = getSampleStyleSheet()
sql_style = ParagraphStyle(
    name="SQLStyle",
    fontName="Courier",
    fontSize=10,
    leading=12,
    spaceAfter=10,
)
content = []

# Add Title to PDF
title = Paragraph("<b><font size=16>RazorX Generated Report</font></b>", styles["Title"])
content.append(title)
content.append(Spacer(1, 20))  # Space below the title

# Iterate over queries and add SQL query, images, and descriptions to PDF
for i in range(1, len(query_samples) + 1):  # Ensure we match the query numbering
    query_filename = f"charts/query{i}.png"
    
    # Add SQL query as a heading
    sql_query_text = sql_queries.get(f"query{i}", "SQL query not available.")
    sql_query_paragraph = Paragraph(f"<b>Query {i}:</b><br/>{sql_query_text}", sql_style)
    content.append(sql_query_paragraph)
    content.append(Spacer(1, 10))  # Space between SQL query and image

    # Add the image
    if os.path.exists(query_filename):
        pil_img = PILImage.open(query_filename)
        img_width, img_height = pil_img.size
        aspect_ratio = img_width / img_height
        new_width = 400  # Set a fixed width
        new_height = new_width / aspect_ratio
        img = Image(query_filename, width=new_width, height=new_height)
        content.append(img)
    else:
        missing_image_msg = Paragraph(f"<b>Image for Query {i} not found.</b>", styles["Normal"])
        content.append(missing_image_msg)
    
    # Add the query description
    description_text = descriptions.get(f"query{i}", "<font color='red'>No description available.</font>")
    paragraph = Paragraph(description_text, styles["Normal"])
    content.append(paragraph)
    content.append(Spacer(1, 20))  # Space between entries
    
    # Add a page break after every query except the last one
    if i != len(query_samples):
        content.append(PageBreak())

# Build the PDF
try:
    doc.build(content)
    print(f"PDF saved as {pdf_filename}")
except Exception as e:
    print(f"Error generating PDF: {e}")