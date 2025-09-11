import streamlit as st
import requests
import json
import os

# Show title and description.
st.title("💬 Poe Chatbot")
st.write(
    "This is a simple chatbot that uses Poe's API to generate responses from GPT-5-mini. "
    "The POE_API_KEY should be set as an environment variable. "
    "You can also store it in `./.streamlit/secrets.toml` for local development."
)

# Get POE API key from environment variable or Streamlit secrets
poe_api_key = os.getenv("POE_API_KEY") or st.secrets.get("POE_API_KEY", "")

if not poe_api_key:
    st.info("Please set the POE_API_KEY environment variable or add it to your Streamlit secrets to continue.", icon="🗝️")
else:
    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using Poe's API
        with st.chat_message("assistant"):
            # Prepare the request to Poe API
            headers = {
                "Authorization": f"Bearer {poe_api_key}",
                "Content-Type": "application/json"
            }
            
            # Format the conversation history for Poe API
            # Note: You may need to adjust this structure based on Poe's actual API format
            data = {
                "model": "GPT-5-mini",  # or however Poe identifies this bot
                "messages": [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                "stream": True  # if Poe supports streaming
            }
            
            try:
                # Make the API request to Poe
                # Note: Replace this URL with the actual Poe API endpoint
                response = requests.post(
                    "https://api.poe.com/v1/chat/completions",  # Placeholder URL
                    headers=headers,
                    json=data,
                    stream=True
                )
                
                if response.status_code == 200:
                    # Handle streaming response
                    response_text = ""
                    placeholder = st.empty()
                    
                    for line in response.iter_lines():
                        if line:
                            try:
                                # Parse the streaming response
                                # Note: Adjust this based on Poe's actual streaming format
                                line_data = json.loads(line.decode('utf-8'))
                                if 'choices' in line_data and line_data['choices']:
                                    delta = line_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        response_text += delta['content']
                                        placeholder.markdown(response_text + "▌")
                            except json.JSONDecodeError:
                                continue
                    
                    # Final response without cursor
                    placeholder.markdown(response_text)
                    
                else:
                    st.error(f"Error from Poe API: {response.status_code} - {response.text}")
                    response_text = "Sorry, I encountered an error while processing your request."
                
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {str(e)}")
                response_text = "Sorry, I couldn't connect to the Poe API."
            
        # Store the assistant's response
        st.session_state.messages.append({"role": "assistant", "content": response_text})
