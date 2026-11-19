import streamlit as st
from openai import OpenAI
import hashlib

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Voice AI Assistant",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ Voice AI Assistant")
st.caption("Your personal AI assistant")

# ---------------- API KEY ----------------
api_key = st.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="Enter your API key"
)

if not api_key:
    st.info("Please enter your OpenAI API key to continue.")
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

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_audio_hash = None
        st.rerun()

    st.caption("Powered by OpenAI")

# ---------------- AI RESPONSE ----------------
def get_ai_response(prompt):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

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
            ] + st.session_state.messages,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        return answer

    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        st.session_state.messages.pop()
        return None


# ---------------- TEXT TO SPEECH ----------------
def speak_response(text):

    try:
        audio = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        st.audio(audio.content, format="audio/mp3")

    except Exception as e:
        st.warning(f"Voice generation error: {e}")


# ---------------- DISPLAY CHAT ----------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------- TEXT INPUT ----------------
prompt = st.chat_input("Ask me anything...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = get_ai_response(prompt)

        if answer:
            st.markdown(answer)

            if voice_enabled:
                speak_response(answer)


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

                voice_prompt = transcription.text

            if voice_prompt.strip():

                st.success(f"You said: {voice_prompt}")

                with st.chat_message("user"):
                    st.markdown(voice_prompt)

                with st.chat_message("assistant"):
                    with st.spinner("AI is thinking..."):
                        answer = get_ai_response(voice_prompt)

                    if answer:
                        st.markdown(answer)

                        if voice_enabled:
                            speak_response(answer)

        except Exception as e:
            st.error(f"Voice input error: {e}")

st.caption("Made with Python, Streamlit and OpenAI")
