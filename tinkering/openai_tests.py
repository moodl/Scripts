import sys
import json
from openai import OpenAI

# JSON should be like this:
#{
#    "api_key": "####",
#    "organization_id": "####",
#    "project_id": "####"
#}

# Loading configuration data from the JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Make sure these values are correct
api_key = config['api_key']
organization_id = config['organization_id']
project_id = config['project_id']

client = OpenAI(
    api_key=api_key,
    organization=organization_id,
    project=project_id,
)

def run_openai_query(query, model="gpt-4o-mini", max_tokens=150, temperature=0.7, top_p=1.0, n=1, stream=True):
    """
    Executes a query to the OpenAI model.

    :param query: The query to be sent to the model.
    :param model: The model to be used. Default is 'gpt-4o-mini'.
    :param max_tokens: The maximum number of tokens for the response. Default is 150.
    :param temperature: Creativity parameter. Values between 0 and 1. Default is 0.7.
    :param top_p: Probability threshold for sampling. Values between 0 and 1. Default is 1.0.
    :param n: Number of generated responses. Default is 1.
    :param stream: If True, the response will be streamed. Default is True.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=stream,
    )
    
    if stream:
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
    else:
        for choice in response.choices:
            print(choice.message["content"])

def main():
    while True:
        try:
            query = input("\nSend message to ChatGPT: ")
            inp = input("Define own parameters? (default: no): ")
            if inp == "yes" or inp == "y":
                model = input("Enter model (default: gpt-4o-mini): ") or "gpt-4o-mini"
                max_tokens = int(input("Enter max tokens (default: 150): ") or 150)
                temperature = float(input("Enter temperature (default: 0.7): ") or 0.7)
                top_p = float(input("Enter top_p (default: 1.0): ") or 1.0)
                n = int(input("Enter number of responses (default: 1): ") or 1)
                stream = input("Stream response? (y/n, default: y): ").lower() in ['y', 'yes', '']
                run_openai_query(query, model=model, max_tokens=max_tokens, temperature=temperature, top_p=top_p, n=n, stream=stream)
            else:
                run_openai_query(query)
        except KeyboardInterrupt:
            print("\nReceived KeyboardInterrupt")
            sys.exit()
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()