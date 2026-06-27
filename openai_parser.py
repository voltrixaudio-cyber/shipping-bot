import json
from openai import OpenAI
from config import Config

class AIParser:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def parse_shipping_details(self, text):
        prompt = f"""
        Extract shipping details from the following text and return a JSON object.
        Text: "{text}"
        
        Required JSON format:
        {{
          "pickup_pincode": int,
          "delivery_pincode": int,
          "weight_grams": int,
          "receiver_name": "string",
          "receiver_phone": "string",
          "pickup_address": "string",
          "delivery_address": "string"
        }}
        
        Note: Convert weight to grams (e.g., 2.5kg = 2500). If any detail is missing, use null.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that parses shipping details into structured JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        return json.loads(response.choices[0].message.content)
