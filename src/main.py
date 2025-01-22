import os
import streamlit as st
from loguru import logger
from langchain_ollama import ChatOllama
import requests
from bs4 import BeautifulSoup


def get_ollama_llm(
        model_name: str,
        temperature: float = 0.8,
    ):
    llm = ChatOllama(
        model=model_name,
        temperature=temperature,
        base_url=os.getenv('OLLAMA_URL'),  # Set the remote server URL
    )
    return llm


def ask_llm(llm, query):
    response = llm.stream(f'{query}')
    return response

def rm_pdf_4m_sess():
    for key in st.session_state.keys():
        if key in st.session_state:
            del st.session_state[key]


def main():
    st.set_page_config(page_title=os.getenv("APP_NAME"))
    st.title(os.getenv("APP_NAME"))
    def chat_callback():
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        user_input = st.session_state.user_input
        logger.info(f'user_input: {user_input}')
        message = {
            "role": "user",
            "content": user_input,
        }
        st.session_state.messages.append(message)
        response_msg = {
            "role": "assistant",
            "content": ask_llm(
                st.session_state.llm,
                f'{st.session_state.mkdwn_4m_pdf}\nQuestion: {user_input}',
            ),
        }
        st.session_state.messages.append(response_msg)

    # Add model selection dropdown
    available_models = ["phi4:latest", "gemma2:latest", ]
    selected_model = st.selectbox("Select AI Model", available_models, index=0)
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = selected_model
        
        
    # # File uploader
    # uploaded_file = st.file_uploader(
    #     "Choose a PDF file", type="pdf", on_change=rm_pdf_4m_sess)

    # if uploaded_file is None:
    #     return
    # # Read the PDF file
    # if 'pdf_file_b' not in st.session_state:
    #     st.session_state.pdf_file_b = uploaded_file.getvalue()
    # pdf_viewer(st.session_state.pdf_file_b, height=900)

    # Create a text input box
    url_input = st.text_input(
        label="Enter your URL:",
        placeholder="https://example.com"
    )

    
    if url_input:
        # st.write(f"You entered: {url_input}")
        with st.spinner('Fetching webpage content...'): 
            try:
                response = requests.get(url_input)
                response.raise_for_status()  # Raise an exception for bad status codes
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text content from the webpage
                webpage_text = soup.get_text(separator='\n', strip=True)
                
                st.write("Successfully fetched webpage content")
                if 'mkdwn_4m_pdf' not in st.session_state:
                    st.session_state.mkdwn_4m_pdf = webpage_text  # Store the webpage content
                
            except Exception as e:
                st.error(f"Error fetching webpage: {str(e)}")
            return
    # import pdb; pdb.set_trace()
    
        # _tf.write(uploaded_file.getvalue())

        # if 'mkdwn_4m_pdf' not in st.session_state:
        #     logger.debug(f'{_tf.name}')
        #     st.session_state.mkdwn_4m_pdf = get_markdown_from_pdf(_tf.name)
        
        
        
        if 'llm' not in st.session_state:
            st.session_state.llm = get_ollama_llm(st.session_state.selected_model)
        llm = st.session_state.llm
        
        if 'general_paper_summary' not in st.session_state:
            st.session_state.general_paper_summary = ask_llm(llm, st.session_state.mkdwn_4m_pdf)

        response_placeholder = st.empty()
        if 'gen_ppr_summ' not in st.session_state:
            gen_ppr_summ = ""
            for chunk in st.session_state.general_paper_summary:
                gen_ppr_summ += chunk.content  # Append each chunk to the response text
                response_placeholder.markdown(gen_ppr_summ)
                st.session_state.gen_ppr_summ = gen_ppr_summ
        else:
            response_placeholder.markdown(st.session_state.gen_ppr_summ)



        st.chat_input(
            "Ask a question about the paper",
            on_submit=chat_callback,
            key='user_input',
        )
        if 'messages' not in st.session_state:
            return
        
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                # Handle rendering of generator, even tho Streamlit handles it automatically
                # but the string needs to be saved back to the message for continuity
                msg = message["content"]
                # check if msg is a generator
                if isinstance(msg, str):
                    st.write(msg)
                else:
                    ai_res_plchldr = st.empty()
                    ai_response = ""
                    for chunk in msg:
                        ai_response += chunk.content  # Append each chunk to the response text
                        ai_res_plchldr.write(ai_response)
                    st.session_state.messages[idx]["content"] = ai_response



if __name__ == "__main__":
    main()