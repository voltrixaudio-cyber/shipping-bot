# AI Shipping Telegram Bot

This bot automates shipping using OpenAI for parsing raw text and Delhivery for logistics.

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   - Copy `.env.example` to `.env`.
   - Fill in your `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, and `DELHIVERY_API_TOKEN`.

3. **Run the Bot (Local):**
   ```bash
   python bot.py
   ```

## Deployment on Render (24/7 Hosting)

This project includes a `render.yaml` blueprint for easy deployment on Render.com.

1.  **Create a GitHub Repository:** Push all the project files (including `render.yaml`) to a new GitHub repository.
2.  **Connect to Render:**
    - Go to [Render.com](https://render.com/) and log in.
    - Create a new "Blueprint" service and connect it to your GitHub repository.
    - Render will automatically detect the `render.yaml` file and configure your service.
3.  **Set Environment Variables:** In your Render service settings, add the following environment variables:
    - `TELEGRAM_BOT_TOKEN`
    - `OPENAI_API_KEY`
    - `DELHIVERY_API_TOKEN`
    - (Optional) `DELHIVERY_API_URL` (defaults to staging if not set)

Render will then build and deploy your bot, keeping it running 24/7.

## Workflow
1. User sends raw shipping text.
2. AI extracts structured data.
3. Bot checks serviceability and calculates rates.
4. User selects "Express" or "Surface".
5. Bot creates shipment and returns tracking/label links.
