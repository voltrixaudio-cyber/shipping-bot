import requests

import json

import logging

from config import Config



# Configure logging

logging.basicConfig(level=logging.INFO, format=\'%(asctime)s - %(levelname)s - %(message)s\')
                    

                    
class DelhiveryClient:
  
    def __init__(self):
      
        self.token = Config.DELHIVERY_API_TOKEN
      
        self.base_url = Config.DELHIVERY_BASE_URL.rstrip(\'/\')
                                                         
        self.headers = {
          
            "Authorization": f"Token {self.token}",
          
            "Content-Type": "application/json"
          
        }
      
        logging.info(f"Initialized DelhiveryClient with base_url: {self.base_url}")
      


    def check_serviceability(self, pincode):
      
        url = f"{self.base_url}/c/api/pin-codes/json/"
      
        params = {"filter_codes": pincode}
      
        try:
          
            logging.info(f"Checking serviceability for pincode: {pincode}")
          
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
          
            logging.info(f"Serviceability Response Status: {response.status_code}")
          
            if response.status_code == 200:
              
                data = response.json()
              
                for item in data.get("delivery_codes", []):
                  
                    if str(item.get("postal_code")) == str(pincode):
                      
                        logging.info(f"Pincode {pincode} is serviceable.")
                      
                        return True
                      
            logging.warning(f"Pincode {pincode} is not serviceable or API error.")
          
        except Exception as e:
          
            logging.error(f"Serviceability Check Error: {e}")
          
        return False
      


    def get_rates(self, o_pin, d_pin, weight_grams):
      
        # Rates API ALWAYS uses production URL for many clients
      
        url = "https://track.delhivery.com/api/kinko/v1/invoice/charges/.json"
      
        rates = {}
      
        pickup_location_name = Config.DELHIVERY_PICKUP_LOCATION_NAME
      


        logging.info(f"Fetching rates from {o_pin} to {d_pin} for {weight_grams}g using client \'{pickup_location_name}\'")
      


        for mode in ["E", "S"]:
          
            params = {
              
                "md": mode,
              
                "ss": "Delivered",
              
                "o_pin": o_pin,
              
                "d_pin": d_pin,
              
                "cgm": weight_grams,
              
                "client": pickup_location_name
              
            }
          
            try:
              
                # Log full request for debugging
              
                logging.info(f"Rates API Request ({mode}): URL={url}, Params={params}")
              
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
              
                logging.info(f"Rates API Response ({mode}): Status {response.status_code}, Content: {response.text}")
              


                if response.status_code == 200:
                  
                    data = response.json()
                  
                    # Response is usually a list

                    if isinstance(data, list) and len(data) > 0:
                      
                        rates[mode] = data[0].get("total_amount", "N/A")
                      
                    else:
                      
                        rates[mode] = "N/A"
                      
                else:
                  
                    rates[mode] = "Error"
                  
            except Exception as e:
              
                logging.error(f"Rates API Exception for mode {mode}: {e}")
              
                rates[mode] = "Error"
              
        return rates
      


    def create_shipment(self, shipment_data):
      
        """
        
        Creates a shipment in Delhivery.
        
        Expects shipment_data to be a dictionary with all required fields.
        
        """
      
        url = f"{self.base_url}/api/cmu/create.json"
      


        # Delhivery expects format=json and data={...} as form-encoded data

        payload = {
          
            "format": "json",
          
            "data": json.dumps(shipment_data)
          
        }



        # For this specific endpoint, we use application/x-www-form-urlencoded

        headers = {
          
            "Authorization": f"Token {self.token}",
          
            "Content-Type": "application/x-www-form-urlencoded"
          
        }



        try:
          
            logging.info(f"Creating shi








































































