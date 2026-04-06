from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "로그인 기능에 대한 QA 테스트 케이스 3개만 작성해줘. 한국어로."}
    ]
)

print(response.choices[0].message.content)
