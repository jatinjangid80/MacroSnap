import json
import requests
from google import genai
from google.genai import types
import streamlit as st

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT


GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
BOT_USERNAME = "MacroSnapjatinbot"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()
MODEL_NAME = "gemini-3.8-flash"


def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        data = response.json()
        if data.get("ok"):
            return True, "Message sent to Telegram!"
        else:
            return False, data.get("description", "Failed to send Telegram message.")
    except Exception as error:
        return False, str(error)


def get_latest_telegram_chat():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("ok") and data.get("result"):
            last_update = data["result"][-1]
            if "message" in last_update:
                chat = last_update["message"]["chat"]
                return str(chat["id"]), chat.get("first_name", "")
        return None, None
    except Exception:
        return None, None


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"


if "messages" not in st.session_state:
    st.session_state.messages = []

# Step 1: Onboarding (Name and Telegram Chat ID)

if "onboarded" not in st.session_state:
    st.title("🥗 MacroSnap")
    st.caption("Snap it. Track it. Send yourself the results on Telegram.")

    st.markdown(
        f"""
        👉 **First time?** Click here to open your bot on Telegram: 
        [**@MacroSnapjatinbot**](https://t.me/{BOT_USERNAME}) and press **Start** (or send any message).
        """
    )

    detected_id, detected_name = get_latest_telegram_chat()

    with st.form("onboarding_form"):
        default_name = detected_name if detected_name else ""
        name = st.text_input("Your name", value=default_name)
        
        default_chat_id = detected_id if detected_id else ""
        telegram_chat_id = st.text_input(
            "Telegram Chat ID",
            value=default_chat_id,
            placeholder="e.g. 95XXXXXX",
            help="Your chat ID with the bot. Send a message to the bot and it will auto-fill!",
        )

        col_submit, col_detect = st.columns([2, 1])
        with col_submit:
            submitted = st.form_submit_button("Let's go 🚀", use_container_width=True)

    if submitted:
        if not name.strip() or not telegram_chat_id.strip():
            st.warning("Please fill in both your name and Telegram Chat ID. (Make sure you messaged @MacroSnapjatinbot on Telegram first!)")
        else:
            st.session_state.name = name.strip()
            st.session_state.telegram_chat_id = telegram_chat_id.strip()
            # Activate Gemini AI
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()

    st.stop()


# Step 2: Main Chat Interface

header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🥗 MacroSnap")

with button_col:
    send_disabled = len(st.session_state.messages) <= 1
    if st.button("📤 Send to Telegram", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your day..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        success, info = send_telegram(st.session_state.telegram_chat_id, summary)
        if success:
            st.success("Sent! Check your Telegram 📲")
        else:
            st.error(f"Couldn't send that: {info}")

st.caption(f"Logged in as {st.session_state.name} • Updates go to Telegram Chat ID: {st.session_state.telegram_chat_id}")

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)


user_input = st.chat_input(
    "Ask a question, or attach a photo of your meal",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Give me the calories and macros.")

    with st.spinner("Crunching the numbers..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)
