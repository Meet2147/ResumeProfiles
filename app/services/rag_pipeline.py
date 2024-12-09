from app.services.embedding_storage import search_vectors
from app.services.model_inference import generate_detailed_response

async def process_query(query):
    retrieved_data = search_vectors(query)
    generated_response = generate_detailed_response(query, retrieved_data)
    print("hit in services for rag pipeline")
    return generated_response
