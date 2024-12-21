from openai import OpenAI
import json 

def infer_policy(text):
    # TOGETHER_API_KEY = "faf49090a3ab68b259d4b7beaaf2e7a42f3f62f6c93220624107f08ad3210b17"
    print('CONTENT TO CLASSIFY:\n')
    print(text)
    print('\nEND OF CONTENT')
    TOGETHER_API_KEY = "54f853e31dcf2a608cdd6a11a05ab5bd3c5212add172fc1a3a9eb557d6da4ab3"
    client = OpenAI(
        api_key=TOGETHER_API_KEY,
        base_url='https://api.together.xyz/v1',
    )
    chat = [
        {
            "role": "system",
            "content": """
              You are an expert cryptocurrency growth marketer with 10 years of experience analyzing the cryptocurrency market. 
              Your task is to evaluate crypto-currency articles and provide insights on potential bitcoin price manipulation or market impact.
              You are a content classifier responsible for analyzing input content based on the following pre-defined policies. 
              Your objective is to determine if the content aligns with any of these policies. 
              For one article you can have multiple labels
              Let us think step by step in every reasoning

              Pre-defined policies: 
                -  "bitcoin_reporting": "The article provides information about bitcoin. bitcoin must be mentioned in the article.",
                -  "bitcoin_price_manipulation": "The article contains claims about bitcoin's price going up or down without credible evidence or reasoning.",
                -  "bitcoin_positive_speculation": "The article presents a reasonable and well-substantiated case for why bitcoin's price may increase.",
                -  "bitcoin_negative_speculation": "The article presents a reasonable and well-substantiated case for why bitcoin's price may decrease."

              Output:
              Return a JSON object with the following structure, dont add anything else, dont comment anything else outside { and }, even ```json:
              {
                "metrics": [
                  {
                    "policy": "Policy Name",
                    "reasoning": "Clarify how specific elements in the content align or do not align with this policy, and explain step by step why this classification is appropriate based on the topic, let us think step by step. Complex reasoning, using much information possible from the article to infer the alignment",
                    "classification": (0 if not in policy, 1 if in policy)
                  },
                  ... (remaining policies. All four policies must be included)
                ]
              }

              ### IMPORTANT ###
              Let us think step by step in each reasoning, mention the information in article that makes you come up with the answer clear and complex as possible

              """
        },
        {
            "role": "user",
            "content": text
        }
    ]
    # print(f'called {model}')
    model ="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    chat_response = client.chat.completions.create(
            model = model,
            messages=chat,
            top_p = 0.2,
            # max_tokens = 6000,
            stream = False,
            # stop = "```"
        )
    try:
        return json.loads(chat_response.choices[0].message.content.strip("```").strip("json"))
    except:
        print('JSON LOAD FAILED')
        print(chat_response.choices[0].message.content)
        print("CAN NOT LOAD ABOVE RESPONSE")
        return {}
    
def infer_sentiment(metric):
    positive_count = 0

    for i in range(len(metric["metrics"])):
        if 'positive' in metric["metrics"][i]["policy"].lower():
            positive_count += int(metric["metrics"][i]["classification"])*1
        elif 'manipulation' in metric["metrics"][i]["policy"].lower():
            positive_count += int(metric["metrics"][i]["classification"])*0.1
        elif 'reporting' in metric["metrics"][i]["policy"].lower():
            positive_count += int(metric["metrics"][i]["classification"])*0.2
        
    # print(positive_count)
    return round(positive_count,4)*100
        

# print(infer_sentiment(['The bitcoin has gone up significantly!']))