from openai import OpenAI
from google import genai
import os
from config.config_loader import load_model_config
config=load_model_config()
from dotenv import load_dotenv
load_dotenv()

api_key=os.getenv("GROQ_API_KEY")
client = OpenAI(api_key=api_key, base_url=config["url"])
class LLMService:
    def invoke(self,input_text):
        response=client.responses.create(
            input=input_text,
            model=config["model"]
        )
        return response.output_text
    

class PlannerLLMService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"

    def invoke(self, input_text):
        response = self.client.models.generate_content(
            model=self.model,
            contents=input_text
        )
        return response
    
    
if __name__ == "__main__":
    llm=LLMService()
    print(llm.invoke("capital of india"))