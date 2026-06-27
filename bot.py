import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import Config
from openai_parser import AIParser
from delhivery_client import DelhiveryClient

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ai_parser = AIParser()
delhivery = DelhiveryClient()

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
        
        # Step 3: Serviceability Check
        await status_msg.edit_text("Checking serviceability... 🔍")
        is_serviceable = delhivery.check_serviceability(details['delivery_pincode'])
        
        if not is_serviceable:
            await status_msg.edit_text(f"Sorry, pincode {details['delivery_pincode']} is not serviceable. ❌")
            return

        # Step 4: Get Shipping Costs
        await status_msg.edit_text("Calculating rates... 💰")
        rates = delhivery.get_rates(details['pickup_pincode'], details['delivery_pincode'], details['weight_grams'])
        
        # Step 5: User Selection
        keyboard = [
            [
                InlineKeyboardButton(f"🚀 Express: ₹{rates.get('E', 'N/A')}", callback_query_data='ship_E'),
                InlineKeyboardButton(f"📦 Surface: ₹{rates.get('S', 'N/A')}", callback_query_data='ship_S')
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
        await status_msg.edit_text("Oops! Something went wrong. Please check your input and try again. ⚠️")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    mode = query.data.split('_')[1]
    details = context.user_data.get('shipping_details')
    
    if not details:
        await query.edit_message_text("Session expired. Please send details again.")
        return

    await query.edit_message_text(f"Creating shipment ({'Express' if mode == 'E' else 'Surface'})... 🚚")
    
    try:
        # Step 6: Create Shipment
        result = delhivery.create_shipment(details, mode)
        
        if result.get('success'):
            shipment = result['packages'][0]
            response_text = (
                f"🎉 **Shipment Created Successfully!**\n\n"
                f"📦 **Waybill:** `{shipment.get('waybill')}`\n"
                f"🔗 [Track Shipment](https://www.delhivery.com/track/package/{shipment.get('waybill')})\n"
                f"📄 [Download Label]({result.get('label_url', '#')})\n"
                f"📍 **Status:** {result.get('status', 'Pending')}"
            )
            await query.edit_message_text(response_text, parse_mode='Markdown')
        else:
            error_msg = result.get('errors', ['Unknown error'])[0]
            await query.edit_message_text(f"❌ **Failed to create shipment:**\n{error_msg}", parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"Shipment Error: {e}")
        await query.edit_message_text("⚠️ Error creating shipment. Please try again later.")

from flask import Flask
import threading

app = Flask(__name__)

@app.route('/health')
def health_check():
    return 'Bot is running', 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    try:
        Config.validate()
        application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        application.add_handler(CallbackQueryHandler(button_callback))
        
        logging.info("Bot is running...")
        application.run_polling()
    except ValueError as e:
        print(f"Configuration Error: {e}")
