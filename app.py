import streamlit as st
import requests

st.title("AI Video Generator 🎥")

user_input = st.text_input("Enter your prompt:")

if st.button("Generate"):
    st.write(f"Generating video for: {user_input}")

import streamlit as st
from groq import Groq

st.title("AI Chat App 🤖")

client = Groq(api_key="yaha_apni_real_api_key_daal")

user_input = st.text_input("Ask something:")

if st.button("Ask"):
    if user_input:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": user_input}],
            model="llama3-8b-8192"
        )
        st.write(response.choices[0].message.content)
