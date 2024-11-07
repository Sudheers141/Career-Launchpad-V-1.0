# test_nvidia_api.py
from openai import OpenAI
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the NVIDIA API client with the masked API key
client = OpenAI(
    api_key=os.getenv("NVIDIA_API_KEY"),  # Load API key from environment
    base_url="https://integrate.api.nvidia.com/v1"
)

def test_nvidia_api():
    try:
        # Sample input for testing
        input_text = "What is the capital of France?"

        # Make API call to get embeddings
        response = client.embeddings.create(
            input=[input_text],
            model="nvidia/nv-embedqa-e5-v5",
            encoding_format="float",
            extra_body={"input_type": "query", "truncate": "NONE"}
        )

        # Retrieve and print the embedding
        embedding = response.data[0].embedding
        print("API call successful. Embedding received:", embedding[:10], "...")  # Print first 10 elements for brevity
        return True

    except Exception as e:
        print("Error during API call:", e)
        return False

# Run the test
if __name__ == "__main__":
    success = test_nvidia_api()
    if success:
        print("NVIDIA API test passed.")
    else:
        print("NVIDIA API test failed.")
