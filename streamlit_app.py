import streamlit as st
import openai
import pysrt
import tiktoken

summary_prompt = """
You have been assigned the role of a professional video summarizer. You will be given a subtitle file with srt format.

Your task is to read through the subtitles, group together coherent topics into main points, and add the next point when you feel the conversation has moved on to the next topic. Your aim is to provide readers with the key points of the video immediately and allow them to jump to specific time points using the time stamps you provide.

When summarizing the points, you must also include the starting time point of the point in the video in the following format:

[(from timestamp) - (to timestamp)] - Summary of the point content.
Example:
[00:06:20,480 - 00:10:12,720] - Explain the unique defensive characteristics of bonds during economic recessions or market turbulence.

Start:

{{your content here}}

The above is summarized into 2 key points. You may use context to determine the point. Respond in Traditional Chinese. You may use context to determine the point.

Please respond in Traditional Chinese.
"""


def count_subtitle_characters(subtitle):
    content = subtitle.text
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(content)
    return len(tokens)


def read_srt_file(srt_text):
    return pysrt.from_string(srt_text, encoding='utf-8')


def subs_to_string(subs):
    ret = ""
    for sub in subs:
        ret += str(sub)
    return ret


def generate_response(message_log, tempe=0.7):
    # Use OpenAI's ChatCompletion API to get the chatbot's response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # The name of the OpenAI chatbot model to use
        messages=message_log,
        temperature=tempe,
    )
    print(response)
    # Find the first response from the chatbot that has text in it (some responses may not have text)
    for choice in response.choices:
        if "text" in choice:
            return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content, response.usage["total_tokens"]


st.title("SummaSub")
st.write("Introducing SummaSub - a revolutionary tool that uses OpenAI to summarize SRT subtitles.")
transcript_name = st.file_uploader(
    "Upload your .srt file", type=['srt'])
col1, col2 = st.columns(2)
openai_key = col1.text_input("OpenAI API Key", type="password")

text_engine_options = ["gpt-3.5-turbo", "text-davinci-003"]
default_text_engine_option = "gpt-3.5-turbo"
text_engine_select = col2.selectbox("Text Engine", options=text_engine_options, index=text_engine_options.index(
    default_text_engine_option), help='Select the Open AI text engine for the summary')
make_button = st.button("Summarize")

if make_button:
    streamlit_progress_bar = st.progress(0)
    streamlit_progress_message = st.markdown(" ")
    content = transcript_name.getvalue().decode("utf-8")
    subs = read_srt_file(content)

    max_characters = 2300  # 修改為預期的最大字符數
    total_characters = 0
    part_subs = []
    file_count = 1
    sub_blocks = []

    for sub in subs:
        characters = count_subtitle_characters(sub)
        total_characters += characters

        if total_characters >= max_characters:
            sub_blocks.append(subs_to_string(part_subs))
            part_subs = [sub]
            total_characters = characters
            file_count += 1
        else:
            part_subs.append(sub)

        #   將剩餘的字幕區塊寫入最後一個文件
    if total_characters > 0:
        sub_blocks.append(subs_to_string(part_subs))
    print(f"Load {len(sub_blocks)} blocks")
    streamlit_progress_message.markdown(
        f"Split file to {len(sub_blocks)} blocks")

    result = ""
    openai.api_key = openai_key
    counter = 0
    result_block = st.code(result)
    for sub_b in sub_blocks:
        streamlit_progress_bar.progress(int((counter/len(sub_blocks))*100))
        streamlit_progress_message.markdown(
            f"Summarize block {counter+1} .")
        user_prompt = summary_prompt.replace("{{your content here}}", sub_b)
        message_log = [
            {"role": "system", "content": "You are ChatGPT, a large language model trained by OpenAI."}]
        message_log.append({"role": "user", "content": user_prompt})
        resp, usage = generate_response(message_log)
        print(resp)
        result += resp + "\n\n"
        counter += 1
        result_block.code(result)
