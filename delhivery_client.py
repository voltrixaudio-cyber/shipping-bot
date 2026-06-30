import requests
import json
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DelhiveryClient:
    def __init__(self):
        self.token = Config.DELHIVERY_API_TOKEN
        self.base_url = Config.DELHIVERY_BASE_URL
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
        # Rates API often uses production URL
        url = "https://track.delhivery.com/api/kinko/v1/invoice/charges/.json"
        
        rates = {}
        pickup_location_name = Config.DELHIVERY_PICKUP_LOCATION_NAME
        logging.info(f"Fetching rates from {o_pin} to {d_pin} for {weight_grams}g using client '{pickup_location_name}'")
        
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
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                logging.info(f"Rates API Response ({mode}): Status {response.status_code}, Content: {response.text}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        rates[mode] = data[0].get("total_amount", "N/A")
                    else:
                        rates[mode] = "N/A"
                else:
                    rates[mode] = "Error"
            except Exception as e:
                logging.error(f"Rates API Error for mode {mode}: {e}")
                rates[mode] = "Error"
        return rates

    def create_shipment(self, details, mode):
        url = f"{self.base_url}/api/cmu/create.json"
        pickup_location_name = Config.DELHIVERY_PICKUP_LOCATION_NAME
        
        payload = {
            "shipments": [{
                "name": details.get("receiver_name"),
                "add": details.get("delivery_address"),
                "pin": details.get("delivery_pincode"),
                "phone": details.get("receiver_phone"),
                "payment_mode": "Pre-paid",
                "order": f"ORD_{str(details.get('receiver_phone', '0000'))[-4:]}",
                "weight": details.get("weight_grams"),
                "shipping_mode": "Express" if mode == "E" else "Surface"
            }],
            "pickup_location": {
                "name": pickup_location_name,
                "pin": details.get("pickup_pincode")
            }
        }
        
        logging.info(f"Creating shipment at {url} with payload: {json.dumps(payload)}")
        
        try:
            data = f"format=json&data={json.dumps(payload)}"
            headers = {
                "Authorization": f"Token {self.token}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=15)
            logging.info(f"Create Shipment Response: Status {response.status_code}, Content: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    packages = result.get("packages", [])
                    waybill = packages[0].get("waybill") if packages else "N/A"
                    return {
                        "success": True,
                        "waybill": waybill,
                        "status": "Created",
                        "tracking_url": f"https://www.delhivery.com/track/package/{waybill}",
                        "label_url": f"https://track.delhivery.com/api/p/labels/print/json/?waybills={waybill}"
                    }
                else:
                    error_msg = result.get("errors", ["API error"])[0]
                    return {"success": False, "error": error_msg}
            else:
                return {"success": False, "error": f"HTTP Status {response.status_code}"}
        except Exception as e:
            logging.error(f"Create Shipment Exception: {e}")
            return {"success": False, "error": str(e)}
