import streamlit as st
import requests

from groq import Groq

import edge_tts
import asyncio
import tempfile

from moviepy.editor import VideoFileClip

st.set_page_config(page_title="Apna Meta AI", page_icon="🎬")
st.title("Apna Meta AI + Video + Voice + Music 🚀")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]
PIXABAY_KEY = st.secrets["PIXABAY_KEY"]

client = Groq(api_key=GROQ_API_KEY)

VOICES = {
    "Narrator Hindi": "hi-IN-MadhurNeural",
    "Character Female": "hi-IN-SwaraNeural",
    "Narrator English": "en-US-GuyNeural"
}

MUSIC_MOODS = {
    "happy": "happy+upbeat", "sad": "sad+piano", "action": "action+epic",
    "calm": "calm+ambient", "scary": "horror+dark", "romantic": "romantic+love"
}

async def text_to_speech(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        await communicate.save(tmp.name)
        return tmp.name

def get_music_for_mood(prompt):
    try:
        mood_resp = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": f"Scene ka mood 1 word: {prompt}. Options: happy,sad,action,calm,scary,romantic. Only 1 word."}]
        )
        mood = mood_resp.choices[0].message.content.lower().strip()
        if mood not in MUSIC_MOODS: mood = "calm"

        url = f"https://pixabay.com/api/videos/music/?key={PIXABAY_KEY}&q={MUSIC_MOODS[mood]}"
        r = requests.get(url, timeout=10).json()
        if r["hits"]:
            music_url = r["hits"][0]["audio"]
            music_data = requests.get(music_url, timeout=20).content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(music_data)
                return tmp.name
    except: return None

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.write(msg["content"])
            if "audio" in msg: st.audio(msg["audio"])
        elif msg["type"] == "video":
            st.video(msg["content"])

col1, col2 = st.columns([3,1])
with col1: prompt = st.chat_input("video banao: scene | bolo: dialogue | kuch bhi pucho")
with col2: voice_choice = st.selectbox("Voice", list(VOICES.keys()))

if prompt:
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        if "video banao" in prompt.lower():
            video_prompt = prompt.replace("video banao:", "").strip()

            with st.status("Bana raha hu... 3-4 min lagega", expanded=True) as status:
                st.write("1/4 Script likh raha...")
                script_resp = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[{"role": "user", "content": f"15 sec Hindi narration for: {video_prompt}. Only narration, no extra text."}]
                )
                narration = script_resp.choices[0].message.content

                st.write("2/4 Video render ho raha...")
                API_URL = "https://api-inference.huggingface.co/models/cerspense/zeroscope_v2_576w"
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                video_resp = requests.post(API_URL, headers=headers, json={"inputs": video_prompt, "parameters": {"num_frames": 50}}, timeout=300)

                st.write("3/4 Voice + Music fetch...")
                voice_path = asyncio.run(text_to_speech(narration, VOICES[voice_choice]))
                music_path = get_music_for_mood(video_prompt)

                st.write("4/4 Sab merge kar raha...")
                if video_resp.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as v_tmp:
                        v_tmp.write(video_resp.content)
                        video_clip = VideoFileClip(v_tmp.name)

                    voice_clip = AudioFileClip(voice_path)
                    if music_path:
                        music_clip = AudioFileClip(music_path).volumex(0.25).set_duration(video_clip.duration)
                        final_audio = CompositeAudioClip([music_clip, voice_clip])
                    else:
                        final_audio = voice_clip

                    final_video = video_clip.set_audio(final_audio)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out_tmp:
                        final_video.write_videofile(out_tmp.name, codec="libx264", audio_codec="aac", logger=None)
                        st.video(out_tmp.name)
                        status.update(label="Ready ✅", state="complete")
                        st.caption(f"**Narration:** {narration}")
                        st.session_state.messages.append({"role": "assistant", "type": "video", "content": out_tmp.name})
                else:
                    st.error("Video API busy. Voice sun lo:")
                    st.audio(voice_path)

        elif "bolo:" in prompt.lower():
            text = prompt.replace("bolo:", "").strip()
            audio_path = asyncio.run(text_to_speech(text, VOICES[voice_choice]))
            st.audio(audio_path)
            st.write(text)
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": text, "audio": audio_path})

        else:
            resp = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = resp.choices[0].message.content
            st.write(reply)
            audio_path = asyncio.run(text_to_speech(reply, VOICES[voice_choice]))
            st.audio(audio_path)
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply, "audio": audio_path})
