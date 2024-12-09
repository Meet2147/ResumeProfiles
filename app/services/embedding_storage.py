from app.config.weaviate import get_weaviate_client

def search_vectors(query):
    client = get_weaviate_client()
    # Replace with the actual search query logic for your Weaviate instance
    results = client.query.get("YourClassName", query).do()
    return results

def generate_vectors(document):
    results = "hi from generate_vectors in service file "
    print("results",results)
    return results