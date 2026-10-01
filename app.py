import json
import requests
from google import genai
from google.genai import types
import streamlit as st

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT


GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
BOT_USERNAME = "MacroSnapjatinbot"

# Reliable production models with automatic fallback
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def init_chat_session(model_name=PRIMARY_MODEL):
    return gemini_client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )


def send_telegram(chat_id, text):
    try:
        raw_id = str(chat_id).strip()
        final_chat_id = int(raw_id) if raw_id.lstrip("-").isdigit() else raw_id
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": final_chat_id, "text": text},
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
    # Ensure chat is initialized
    if "chat" not in st.session_state or st.session_state.chat is None:
        st.session_state.chat = init_chat_session(PRIMARY_MODEL)

    try:
        response = st.session_state.chat.send_message(parts)
        return response.text
    except Exception as error:
        # If primary model fails with 503 or overload, retry with fallback model
        try:
            st.session_state.chat = init_chat_session(FALLBACK_MODEL)
            response = st.session_state.chat.send_message(parts)
            return response.text
        except Exception as fallback_error:
            return f"Sorry, something went wrong: {fallback_error}"


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
            placeholder="e.g. 8347561256",
            help="Your chat ID with the bot. Send a message to @MacroSnapjatinbot and it auto-fills!",
        )

        submitted = st.form_submit_button("Let's go 🚀", use_container_width=True)

    if submitted:
        if not name.strip() or not telegram_chat_id.strip():
            st.warning("Please fill in both your name and Telegram Chat ID. (Make sure you messaged @MacroSnapjatinbot on Telegram first!)")
        else:
            st.session_state.name = name.strip()
            st.session_state.telegram_chat_id = telegram_chat_id.strip()
            st.session_state.chat = init_chat_session(PRIMARY_MODEL)
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()

    st.stop()


# Step 2: Main Chat Interface

header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🥗 MacroSnap")

with button_col:
    if st.button("📤 Send to Telegram", use_container_width=True):
        if len(st.session_state.messages) <= 1:
            st.info("💡 Please log a meal first (send a photo or description below) so I have something to summarize!")
        else:
            with st.spinner("Summarizing your meals..."):
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
    st.rerun()
