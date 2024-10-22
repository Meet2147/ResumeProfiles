# from services.rag_pipeline import process_query
from services.model_inference import query_profiles, generate_detailed_response

async def process_user_message(user_query: str):
    print("hit in chat controller")
    
    # Query profiles based on user query
    response_query_profiles = await query_profiles(user_query)
    
    # Call generate_detailed_response with both the query and profiles
    result = await generate_detailed_response(user_query, response_query_profiles)
    
    print(result)
    return result
