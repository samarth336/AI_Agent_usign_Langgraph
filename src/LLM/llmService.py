from openai import OpenAI
from google import genai
import os
from typing import cast
from openai.types.chat import ChatCompletionMessageParam
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
    
class PlannerLLMServiceHF:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("HF_TOKEN"), 
                            base_url="https://router.huggingface.co/v1")
    def invoke(self, input_text):
        # Handle both string input and message objects from ChatPromptTemplate
        if isinstance(input_text, str):
            messages = [{"role": "user", "content": input_text}]
        else:
            # Convert message objects to API format with proper role mapping
            messages = []
            for msg in input_text:
                # Map LangChain message types to OpenAI roles
                role_map = {"human": "user", "ai": "assistant", "system": "system"}
                role = role_map.get(msg.type, msg.type)
                
                # Ensure content is not empty
                content = msg.content if msg.content else ""
                if not content:
                    continue  # Skip empty messages
                
                messages.append({"role": role, "content": content})
        
        response = self.client.chat.completions.create(
            model="zai-org/GLM-4.7",
            messages=cast(list[ChatCompletionMessageParam], messages)
        )
        return response.choices[0].message.content
