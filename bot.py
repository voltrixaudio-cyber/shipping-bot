import logging
import os
import asyncio
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
        
        # Validation Check
        if not details.get('pickup_pincode') or not details.get('delivery_pincode'):
            await status_msg.edit_text("⚠️ Could not extract pincodes. Please provide both pickup and delivery pincodes.")
            return

        # Step 4: Get Shipping Costs
        await status_msg.edit_text("Calculating rates... 💰")
        try:
            rates = delhivery.get_rates(details['pickup_pincode'], details['delivery_pincode'], details.get('weight_grams', 500))
        except Exception as e:
            logging.error(f"Rate API Error: {e}")
            rates = {"E": "Error", "S": "Error"}
        
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
            f"📍 From: {details.get('pickup_pincode', 'N/A')}\n"
            f"📍 To: {details.get('delivery_pincode', 'N/A')}\n"
            f"⚖️ Weight: {details.get('weight_grams', 'N/A')}g\n"
            f"👤 Receiver: {details.get('receiver_name', 'N/A')}\n"
            f"📞 Phone: {details.get('receiver_phone', 'N/A')}\n\n"
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
        await query.edit_message_text("Session expired. Please send details again.")
        return
        
    status_msg = await query.edit_message_text(f"Creating shipment ({'Express' if mode == 'E' else 'Surface'})... 📦")
    
    # Step 6: Create Shipment with timeout/error handling
    try:
        # Wrap in try-except to prevent hanging
        result = delhivery.create_shipment(details, mode)
        
        if result.get('success'):
            response = (
                f"🎉 **Shipment Created!**\n\n"
                f"🆔 **Waybill:** `{result['waybill']}`\n"
                f"🚚 **Status:** {result['status']}\n\n"
                f"🔗 [Track Shipment]({result['tracking_url']})\n"
                f"📄 [Download Label]({result['label_url']})"
            )
            await status_msg.edit_text(response, parse_mode='Markdown')
        else:
            error_msg = result.get('error', 'Unknown error from Delhivery API')
            await status_msg.edit_text(f"❌ **Failed to create shipment:**\n`{error_msg}`")
    except Exception as e:
        logging.error(f"Shipment Creation Error: {e}")
        await status_msg.edit_text(f"❌ **Error during shipment creation:**\n`{str(e)}`")

if __name__ == '__main__':
    # Start health check server
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram Bot
    token = Config.TELEGRAM_BOT_TOKEN
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    application.run_polling()
