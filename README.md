# 🥗 MacroSnap

> **Snap it. Track it. Send your nutrition summary straight to Telegram.**

MacroSnap is an AI-powered nutrition buddy built with **Streamlit** and **Google Gemini Vision**. Upload a photo of your meal or describe what you ate, get instant calorie & macro estimates, and send a complete daily summary to your **Telegram** with one click.

---

## 🚀 Features

- 📸 **AI Food Recognition:** Snap a photo of any meal or type a description to estimate calories and protein/carbs/fats.
- 💬 **Interactive Chat:** Ask follow-up questions about nutrition and fitness.
- 📲 **Telegram Integration:** Seamlessly receive your daily meal summaries directly on Telegram via your own bot.
- 🛡️ **Auto-Fallback Engine:** Built-in resilience using `gemini-2.5-flash` with automatic fallback to prevent downtime.

---

## 🛠️ Quickstart / How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/jatinjangid80/MacroSnap.git
cd MacroSnap
```

### 2. Set up virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a secrets file at `.streamlit/secrets.toml`:
```bash
mkdir -p .streamlit
touch .streamlit/secrets.toml
```

Add your API keys inside `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-gemini-api-key"
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
```

> **Where to get keys:**
> - **Gemini API Key:** Get free from [Google AI Studio](https://aistudio.google.com/).
> - **Telegram Bot Token:** Open Telegram, message [@BotFather](https://t.me/BotFather), send `/newbot`, and copy your bot token.

### 5. Start the App
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser!

---

## 📱 How to use Telegram Delivery

1. Open your bot on Telegram and tap **Start** (or send `hello`).
2. Open the MacroSnap app and enter your name and **Telegram Chat ID**.
3. Log your meals with photos or text.
4. Click **📤 Send to Telegram** to get your formatted breakdown!

---

## 📄 License
MIT License. Built with ❤️ using Google Gemini & Streamlit.
