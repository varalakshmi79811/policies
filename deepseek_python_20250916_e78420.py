def chat_assistant_page():
    st.markdown('<div class="section-header">AI Policy Assistant</div>', unsafe_allow_html=True)
    st.write("Chat with your AI assistant to manage policies using natural language.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI Policy Assistant. I can help you:\n\n• View policies: 'Show me all HR policies'\n• Create policies: 'Add a new IT policy called Security Guidelines'\n• Search policies: 'Find policies about remote work'\n• Update policies: 'Update the leave policy'\n• Get statistics: 'Show me policy statistics'\n\nTry saying: 'Add a new HR policy called Test Policy for All Employees about remote work guidelines'"
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
            
    attached_files = st.file_uploader(
        "Attach documents (optional)",
        accept_multiple_files=True,
        type=['pdf', 'doc', 'docx', 'txt']
    )

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Processing your request..."):
            response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
