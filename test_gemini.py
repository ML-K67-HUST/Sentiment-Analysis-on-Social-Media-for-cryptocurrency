from google import genai

client = genai.Client(api_key="AIzaSyDE-n235iHhJMCE7tH4CLzg2JR7lnAx0vo")
response = client.models.generate_content(model="gemini-2.5-flash", contents="Explain how AI works in a few words")

print(response.text)