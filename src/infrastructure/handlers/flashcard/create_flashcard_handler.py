import json

def handler(event, context):
    # Flashcard creation not yet implemented in infrastructure.
    # Return 501 to avoid runtime errors until repo/mapper are available.
    return {
        "statusCode": 501,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"error": "Create flashcard endpoint not implemented."}),
    }
