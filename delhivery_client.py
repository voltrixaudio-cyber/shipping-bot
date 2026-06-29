import requests
import json
from config import Config

class DelhiveryClient:
    def __init__(self):
        self.token = Config.DELHIVERY_API_TOKEN
        self.base_url = Config.DELHIVERY_BASE_URL
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json"
        }

    def check_serviceability(self, pincode):
        url = f"{self.base_url}/c/api/pin-codes/json/"
        params = {"filter_codes": pincode}
        response = requests.get(url, params=params, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            # Check if pincode exists in the delivery_codes list
            for item in data.get("delivery_codes", []):
                if str(item.get("postal_code")) == str(pincode):
                    return True
        return False

    def get_rates(self, o_pin, d_pin, weight_grams):
        # Rates API often uses production URL even in staging docs sometimes
        url = f"https://track.delhivery.com/api/kinko/v1/invoice/charges/.json"
        
        rates = {}
        pickup_location_name = Config.DELHIVERY_PICKUP_LOCATION_NAME
        for mode in ["E", "S"]:
            params = {
                "md": mode,
                "ss": "Delivered",
                "o_pin": o_pin,
                "d_pin": d_pin,
                "cgm": weight_grams,
                "client": pickup_location_name
            }
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    rates[mode] = data[0].get("total_amount", "N/A")
                else:
                    rates[mode] = "N/A"
            else:
                rates[mode] = "Error"
        return rates

    def create_shipment(self, details, mode):
        url = f"{self.base_url}/api/cmu/create.json"
        
        payload = {
            "shipments": [{
                "name": details["receiver_name"],
                "add": details["delivery_address"],
                "pin": details["delivery_pincode"],
                "phone": details["receiver_phone"],
                "payment_mode": "Pre-paid",
                "order": f"ORD_{details['receiver_phone'][-4:]}",
                "weight": details["weight_grams"],
                "shipping_mode": "Express" if mode == "E" else "Surface"
            }],
            "pickup_location": {
                "name": pickup_location_name,
                "pin": details["pickup_pincode"]
            }
        }
        
        data = f"format=json&data={json.dumps(payload)}"
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url, data=data, headers=headers)
        return response.json()
