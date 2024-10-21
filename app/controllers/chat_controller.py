from app.services.rag_pipeline import process_query

async def process_user_message(request):
    user_query = request.message
    print("hit in chat controller")
    result = await process_query(user_query)
    return result
