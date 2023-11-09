import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from config import settings



def use_openai(model:str,message:list,temperature:float,stream:bool = False):
    from openai import OpenAI
    client = OpenAI(
        api_key=settings.openai_api_key,
        organization=settings.openai_organization
    )
    completion = client.chat.completions.create(
        model=model,
        messages=message,
        stream = stream,
        temperature=temperature
    )
    if not stream:
        return completion.choices[0].message.content
    return completion

# if __name__ == "__main__":
#     messages=[
#         {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
#         {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
#     ]
#     response = use_openai(model="gpt-4-1106-preview",message=messages,temperature=0,stream = True)
#     for i in response:
#         print(i.choices[0].delta.content)