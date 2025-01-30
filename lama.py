import streamlit as st
import base64
from groq import Groq
from PIL import Image
import io
import time
from io import BytesIO
from PIL import ImageGrab

# Initialize the Groq client and session state
if 'client' not in st.session_state:
    API_KEY = "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"
    st.session_state.client = Groq(api_key=API_KEY)

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize image storage
if 'current_image' not in st.session_state:
    st.session_state.current_image = None

# Function to clear chat history
def clear_chat():
    st.session_state.messages = []
    st.session_state.current_image = None
    st.rerun()  # Using st.rerun() instead of experimental_rerun()

# Page config
st.set_page_config(page_title="GPT", layout="wide")

# Custom CSS for ChatGPT-like interface
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #f7f7f8;
    }
    .assistant-message {
        background-color: white;
    }
    .chat-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem;
        background-color: white;
    }
    .uploaded-image {
        max-width: 300px;
        max-height: 300px;
        margin: 1rem 0;
    }
    div[data-testid="stSidebarUserContent"] {
        padding-top: 0rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 0.5rem;
        background-color: #f7f7f8;
        color: #444;
        border: 1px solid #ddd;
    }
    .stButton button:hover {
        background-color: #e7e7e8;
        border: 1px solid #ccc;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar with clear chat button
with st.sidebar:
    if st.button("Clear Chat", key="clear_chat"):
        clear_chat()

# Main title
st.title("ChatGPT-like Interface")

# Chat container
chat_container = st.container()

# Display chat history
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "image" in message:
                st.image(message["image"], use_container_width=True)

# Input section (at the bottom)
with st.container():
    col1, col2 = st.columns([3, 1])
    
    with col2:
        image_input_option = st.radio(
            "Image input:",
            ("None", "Upload", "URL", "Paste"),
            horizontal=True
        )
        
        if image_input_option == "Upload":
            uploaded_file = st.file_uploader("Upload image:", type=["jpeg", "jpg", "png"])
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.session_state.current_image = image
                st.image(image, use_container_width=True)
                
        elif image_input_option == "URL":
            image_url = st.text_input("Image URL:", placeholder="https://example.com/image.jpg")
            if image_url:
                try:
                    st.session_state.current_image = image_url
                    st.image(image_url, use_container_width=True)
                except Exception as e:
                    st.error("Invalid image URL")
        
        elif image_input_option == "Paste":
            st.write("Press Ctrl+V to paste an image")
            if st.button("Paste Image"):
                try:
                    image = ImageGrab.grabclipboard()
                    if image:
                        st.session_state.current_image = image
                        st.image(image, use_container_width=True)
                    else:
                        st.error("No image found in clipboard")
                except Exception as e:
                    st.error(f"Error pasting image: {e}")

    with col1:
        # Chat input
        if prompt := st.chat_input("What's on your mind?"):
            # Add user message to chat history
            user_message = {"role": "user", "content": prompt}
            if st.session_state.current_image:
                if isinstance(st.session_state.current_image, Image.Image):
                    # Convert PIL Image to base64
                    buffered = io.BytesIO()
                    st.session_state.current_image.save(buffered, format="JPEG")
                    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    image_payload = {"url": f"data:image/jpeg;base64,{encoded_image}"}
                    user_message["image"] = st.session_state.current_image
                else:
                    # Use URL directly
                    image_payload = {"url": st.session_state.current_image}
                    user_message["image"] = st.session_state.current_image

            st.session_state.messages.append(user_message)

            # Show user message
            with st.chat_message("user"):
                st.write(prompt)
                if "image" in user_message:
                    st.image(user_message["image"], use_container_width=True)

            # Get assistant response
            try:
                message_content = [{"type": "text", "text": prompt}]
                if st.session_state.current_image:
                    message_content.append({"type": "image_url", "image_url": image_payload})

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Make API call
                    completion = st.session_state.client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[{"role": "user", "content": message_content}],
                        temperature=1,
                        max_tokens=1024,
                        top_p=1,
                        stream=True,
                    )

                    # Simulate typing effect
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                            time.sleep(0.01)
                    
                    message_placeholder.markdown(full_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )

            except Exception as e:
                st.error(f"An error occurred: {e}")

            # Clear current image after processing
            st.session_state.current_image = None
