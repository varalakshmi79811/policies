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
    
    st.markdown("---")
    st.markdown('<div class="section-header">Quick Actions</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    action_buttons = [
        ("Show All Policies", "Show me all policies"),
        ("Create Test Policy", "Add a new HR policy called 'Quick Test Policy' for All Employees about testing the system"),
        ("HR Policies", "Show me all HR policies"),
        ("Statistics", "Show me policy statistics")
    ]
    
    for i, (label, command) in enumerate(action_buttons):
        with [col1, col2, col3, col4][i]:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                response = enhanced_chat_with_ai(command, attached_files=attached_files)
                st.session_state.messages.append({"role": "user", "content": command})
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    with st.expander("Example Commands"):
        st.markdown("""
        **Create Policies:**
        - Add a new HR policy called 'Remote Work Guidelines' for All Employees
        - Create an IT policy about password security for IT Department
        - Add a Customer policy called 'Service Standards' for Customer Service Team
        
        **View Policies:**
        - Show me all policies
        - List all HR policies 
        - Find policies about security
        
        **Get Information:**
        - How many policies do we have?
        - Show me expired policies
        - What's the system status?
        """)
