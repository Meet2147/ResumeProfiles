import openai
import os
openai.api_key = os.getenv("openai_api_key")
def generate_response(query, context):
    # Call OpenAI or Hugging Face API with the query and context
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{context} {query}",
        max_tokens=150
    )
    return response.choices[0].text
