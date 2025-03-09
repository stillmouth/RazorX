from transformers import T5ForConditionalGeneration, T5Tokenizer
import os

# Disable warning related to symlinks for Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load pre-trained T5 model and tokenizer
model_name = "t5-small"  # You can try 't5-base' or 't5-large' for better accuracy
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)

def convert_text_to_sql(transcription):
    # Prepend 'translate English to SQL: ' to instruct the model to generate SQL
    input_text = "translate English to SQL: " + transcription

    # Tokenize the input text
    inputs = tokenizer.encode(input_text, return_tensors="pt")

    # Generate the SQL query using the model
    outputs = model.generate(inputs, max_length=50, num_beams=5, early_stopping=True)

    # Decode and return the SQL query
    sql_query = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql_query

if __name__ == "__main__":
    # Example: Pass the transcription text from the frontend or backend
    transcription_text = "What are the total sales for the last quarter?"
    sql_query = convert_text_to_sql(transcription_text)

    print("Generated SQL Query:", sql_query)
