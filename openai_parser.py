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
          "pickup_pincode": int or null,
          "delivery_pincode": int or null,
          "weight_grams": int or null,
          "receiver_name": "string or null",
          "receiver_phone": "string or null",
          "pickup_address": "string or null",
          "delivery_address": "string or null"
        }}
        
        Rules for extraction:
        1. **Weight:** Convert to grams. If "100g" is mentioned, use 100. If "2.5kg" is mentioned, use 2500.
        2. **Pincodes:** Look for 6-digit Indian pincodes. If a pincode is near the word "pickup" or "from", map it to "pickup_pincode".
        3. **Receiver:** Extract the person's name and phone number if provided.
        4. **Addresses:** Extract full address strings if possible.
        5. **Nulls:** If any detail is absolutely not found, use null.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional logistics assistant that extracts shipping data with 100% accuracy into JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        return json.loads(response.choices[0].message.content)
