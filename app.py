import streamlit as st

st.title("My AI App is Working 🚀")

st.write("अगर ये दिख रहा है, तो app सही deploy हो गया 👍")
import streamlit as st
import requests

st.title("AI Video Generator 🎥")

user_input = st.text_input("Enter your prompt:")

if st.button("Generate"):
    st.write(f"Generating video for: {user_input}")
