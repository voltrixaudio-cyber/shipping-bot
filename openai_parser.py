import json

import logging

import time

from typing import Dict, Any, Optional

from openai import OpenAI, APIError, RateLimitError, APIConnectionError



logger = logging.getLogger(__name__)





class AIParser:
  
    """Parse shipping details using OpenAI's GPT-4o model"""
  


    def __init__(self, model: str = "gpt-4o", max_retries: int = 3):
      
        """
        
        Initialize AI Parser.
        


        Args:
        
            model: OpenAI model to use
            
            max_retries: Number of times to retry on transient failures
            
        """
      
        from config import Config
      


        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
      
        self.model = model
      
        self.max_retries = max_retries
      


        logger.info(f"✅ AIParser initialized | Model: {model} | Retries: {max_retries}")
      


    def parse_shipping_details(self, user_text: str) -> Dict[str, Any]:
      
        """
        
        Extract shipping details from user input using AI.
        


        Args:
        
            user_text: User's message containing shipping details
            


        Returns:
        
            Dictionary with parsed shipping details
            


        Raises:
        
            ValueError: If parsing fails after retries
            
        """
      
        if not user_text or not user_text.strip():
          
            logger.error("Empty input text")
          
            raise ValueError("Input text cannot be empty")
          


        logger.info(f"🤖 Parsing shipping details from text ({len(user_text)} chars)")
      


        prompt = self._build_prompt(user_text)
      


        for attempt in range(1, self.max_retries + 1):
          
            try:
              
                logger.debug(f"OpenAI API call attempt {attempt}/{self.max_retries}")
              


                response = self.client.chat.completions.create(
                  
                    model=self.model,
                  
                    messages=[
                      
                        {
                          
                            "role": "system",
                          
                            "content": (
                              
                                "You are a professional logistics assistant that extracts "
                              
                                "shipping data with 100% accuracy into JSON format. "
                              
                                "Always return valid JSON only, no additional text."
                              
                            ),
                          
                        },
                      
                        {"role": "user", "content": prompt},
                      
                    ],
                  
                    response_format={"type": "json_object"},
                  
                    temperature=0.3,
                  
                    timeout=30,
                  
                )
              


                if not response or not response.choices:
                  
                    logger.error(
                      
                        f"❌ Empty choices in OpenAI response (attempt {attempt})"
                      
                    )
                  
                    if attempt == self.max_retries:
                      
                        raise ValueError(
                          
                            "AI parsing failed: No choices returned from OpenAI."
                          
                        )
                      
                    time.sleep(1)
                  
                    continue
                  


                content = response.choices[0].message.content
              


                if not content:
                  
                    logger.error(
                      
                        f"❌ Empty/None content from OpenAI (attempt {attempt})"
                      
                    )
                  
                    if attempt == self.max_retries:
                      
                        raise ValueError(
                          
                            "AI parsing failed: Empty response from OpenAI."
                          
                        )
                      
                    time.sleep(1)
                  
                    continue
                  


                logger.debug(f"Raw OpenAI response: {content[:200]}...")
              


                parsed = json.loads(content)
              
                l







































































