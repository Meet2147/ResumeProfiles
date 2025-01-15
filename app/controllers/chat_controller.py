# from services.rag_pipeline import process_query
from app.services.model_inference import query_profiles, generate_detailed_response

# (request.role, request.message)
async def process_user_message(role:str, user_query: str):
    print("hit in chat controller",role,user_query)
    
    # Query profiles based on user query
    response_query_profiles = await query_profiles(user_query)
    
    # Call generate_detailed_response with both the query and profiles
    result = await generate_detailed_response(role,user_query, response_query_profiles)
    
    print("result from controller =>",result)
    return result
