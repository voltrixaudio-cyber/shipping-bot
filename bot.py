import logging

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import Config

from openai_parser import AIParser

from delhivery_client import DelhiveryClient

from flask import Flask

import threading



# Enable logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)



ai_parser = AIParser()

delhivery = DelhiveryClient()



# Health check server for Render

app = Flask(__name__)

@app.route('/')

def health_check():
    
    return "OK", 200
    


def run_flask():
    
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await update.message.reply_text(
        
        "Welcome to the AI Shipping Bot! 🚀\n\n"
        
        "Send me your shipping details in plain text, like:\n"
        
        "'Pickup from Bangalore 560001, deliver to Mumbai 400001, weight 2.5kg, receiver Priya Sharma, phone 9876543210'"
        
    )
    


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_text = update.message.text
    
    status_msg = await update.message.reply_text("Parsing details with AI... 🤖")
    


    try:
        
        # Step 2: AI Parsing
        
        details = ai_parser.parse_shipping_details(user_text)
        
        context.user_data['shipping_details'] = details
        


        # Step 3: Serviceability Check (Bypassed for testing)

        await status_msg.edit_text("Checking serviceability... 🔍")
        
        # is_serviceable = delhivery.check_serviceability(details['delivery_pincode'])

        # if not is_serviceable:

        #     await status_msg.edit_text(f"Sorry, pincode {details['delivery_pincode']} is not serviceable. ❌")

        #     return



        # Step 4: Get Shipping Costs

        await status_msg.edit_text("Calculating rates... 💰")
        
        rates = delhivery.get_rates(details['pickup_pincode'], details['delivery_pincode'], details['weight_grams'])
        


        # Step 5: User Selection

        keyboard = [
            
            [
                
                InlineKeyboardButton(f"🚀 Express: ₹{rates.get('E', 'N/A')}", callback_data='ship_E'),
                
                InlineKeyboardButton(f"📦 Surface: ₹{rates.get('S', 'N/A')}", callback_data='ship_S')
                
            ]
            
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        


        summary = (
            
            f"✅ **Details Extracted:**\n"
            
            f"📍 From: {details['pickup_pincode']}\n"
            
            f"📍 To: {details['delivery_pincode']}\n"
            
            f"⚖️ Weight: {details['weight_grams']}g\n"
            
            f"👤 Receiver: {details['receiver_name']}\n"
            
            f"📞 Phone: {details['receiver_phone']}\n\n"
            
            f"Please select your shipping mode:"
            
        )
        


        await status_msg.delete()
        
        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
        


    except Exception as e:
        
        logging.error(f"Error: {e}")
        
        await status_msg.edit_text(f"Oops! Something went wrong: {str(e)} ⚠️")
        


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    
    await query.answer()
    


    mode = query.data.split('_')[1]
    
    details = context.user_data.get('shipping_details')
    


    if not details:
        
        await query.edit_message_text("Session expired. Please sen














































