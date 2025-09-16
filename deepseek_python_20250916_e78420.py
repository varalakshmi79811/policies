def chat_assistant_page():
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <div class="section-header">AI Policy Assistant</div>
        <div style="display: flex; gap: 10px;">
            <div style="padding: 8px 12px; background-color: #f8f9fa; border-radius: 6px; font-size: 14px;">
                <span style="color: #28a745;">●</span> Online
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Interact with the AI assistant to manage policies using natural language commands.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI Policy Assistant. I can help you:\n\n• View policies: 'Show me all HR policies'\n• Create policies: 'Add a new IT policy called Security Guidelines'\n• Search policies: 'Find policies about remote work'\n• Update policies: 'Update the leave policy'\n• Get statistics: 'Show me policy statistics'"
            }
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        message_class = "user-message" if message["role"] == "user" else ""
        st.markdown(f"""
        <div class="chat-message {message_class}">
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    
    # Create a custom chat input with file attachment button
    col1, col2 = st.columns([6, 1])
    
    with col1:
        chat_input = st.text_input(
            "Type your message...", 
            key="chat_input",
            label_visibility="collapsed",
            placeholder="Type your message..."
        )
    
    with col2:
        st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
        file_attachment = st.button("📎", use_container_width=True, help="Attach files")
    
    # Handle file upload when attachment button is clicked
    attached_files = None
    if file_attachment:
        attached_files = st.file_uploader(
            "Attach documents",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'txt'],
            key="file_uploader",
            label_visibility="collapsed"
        )
        if attached_files:
            st.info(f"{len(attached_files)} file(s) attached")
    
    # Process chat input
    if chat_input:
        st.session_state.messages.append({"role": "user", "content": chat_input})
        
        with st.spinner("Processing..."):
            response = enhanced_chat_with_ai(chat_input, attached_files=attached_files)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Clear the chat input and file attachments
            st.session_state.chat_input = ""
            if "file_uploader" in st.session_state:
                st.session_state.file_uploader = None
            st.rerun()