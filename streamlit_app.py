cat << 'EOF' > streamlit_app.py
import hashlib
import os
import streamlit as st
from openai import OpenAI

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Voice AI Assistant",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ Voice AI Assistant")
st.caption("Your personal AI assistant")


# ---------------- API KEY ----------------
def get_api_key():
    if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
        return str(st.secrets["OPENAI_API_KEY"]).strip()
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key.strip()
    return None


api_key = get_api_key()

if not api_key:
    st.error("OPENAI_API_KEY नहीं मिली। कृपया `.streamlit/secrets.toml` या Streamlit Cloud Secrets में `OPENAI_API_KEY` सेट करें।")
    st.code('OPENAI_API_KEY = "aapki-nayi-key"', language="toml")
    st.stop()

client = OpenAI(api_key=api_key)

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# ---------------- SETTINGS ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    voice_enabled = st.toggle("Enable AI Voice", value=True)
    autoplay_voice = st.toggle("Auto-play AI Voice", value=True)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_audio_hash = None
        st.rerun()

    st.caption("Powered by OpenAI")


# ---------------- HELPER FUNCTIONS ----------------
def generate_speech(text):
    try:
        audio = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return audio.content
    except Exception as e:
        st.warning(f"Voice generation error: {e}")
        return None


def get_ai_response(prompt, enable_voice=True):
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "audio": None
    })

    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful personal voice assistant. "
                        "Understand Hindi, English and Hinglish. "
                        "Give clear and friendly answers."
                    )
                }
            ] + chat_history,
            temperature=0.7
        )

        answer = response.choices[0].message.content
        audio_bytes = generate_speech(answer) if enable_voice else None

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "audio": audio_bytes
        })

        return answer, audio_bytes

    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        st.session_state.messages.pop()
        return None, None


# ---------------- DISPLAY CHAT ----------------
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("audio"):
            is_latest_assistant = (
                message["role"] == "assistant"
                and idx == len(st.session_state.messages) - 1
            )
            st.audio(
                message["audio"],
                format="audio/mp3",
                autoplay=(autoplay_voice and is_latest_assistant)
            )


# ---------------- TEXT INPUT ----------------
prompt = st.chat_input("Ask me anything...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, audio_bytes = get_ai_response(prompt, enable_voice=voice_enabled)

        if answer:
            st.markdown(answer)
            if audio_bytes:
                st.audio(
                    audio_bytes,
                    format="audio/mp3",
                    autoplay=autoplay_voice
                )


# ---------------- VOICE INPUT ----------------
st.divider()
st.subheader("🎤 Talk to your AI Assistant")

audio_file = st.audio_input("Tap to record your voice")

if audio_file:
    audio_bytes = audio_file.getvalue()
    audio_hash = hashlib.sha256(audio_bytes).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash

        try:
            with st.spinner("Understanding your voice..."):
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=(
                        "recording.wav",
                        audio_bytes,
                        "audio/wav"
                    )
                )

                voice_prompt = (transcription.text or "").strip()

            if voice_prompt:
                st.success(f"You said: {voice_prompt}")

                with st.chat_message("user"):
                    st.markdown(voice_prompt)

                with st.chat_message("assistant"):
                    with st.spinner("AI is thinking..."):
                        answer, reply_audio = get_ai_response(
                            voice_prompt,
                            enable_voice=voice_enabled
                        )

                    if answer:
                        st.markdown(answer)
                        if reply_audio:
                            st.audio(
                                reply_audio,
                                format="audio/mp3",
                                autoplay=autoplay_voice
                            )

        except Exception as e:
            st.error(f"Voice input error: {e}")

st.caption("Made with Python, Streamlit and OpenAI")
EOF
