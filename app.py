import streamlit as st
from groq import Groq
import base64
import io
from streamlit_paste_button import paste_image_button

st.set_page_config(page_title="EOB Decoder", page_icon="🏥")

st.title("EOB Decoder")
st.write("Upload or paste images of your EOB — get a plain English summary.")

SYSTEM_PROMPT = """You are a healthcare benefits expert who helps patients understand their Explanation of Benefits (EOB) documents.

When given an EOB, explain it clearly in plain English using these sections:

**What happened:** A one-sentence summary of what this EOB is about.

**What was covered:** What your insurance paid for and how much.

**What was not covered:** Anything denied or excluded, and the reason.

**What you owe:** The exact amount the patient is responsible for and why.

**Next steps:** Any action the patient should take (pay a bill, appeal a denial, etc.).

Use simple language. Avoid medical and insurance jargon. If something is unclear or missing from the EOB, say so."""

if "pasted_images" not in st.session_state:
    st.session_state.pasted_images = []

if "eob_text" not in st.session_state:
    st.session_state.eob_text = ""


def image_to_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def decode_images(images_b64):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    content = []
    for img_data in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_data}"}
        })
    content.append({
        "type": "text",
        "text": "Please decode this EOB document and explain it in plain English."
    })
    response = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content


tab1, tab2 = st.tabs(["Images", "Paste Text"])

with tab1:
    uploaded_files = st.file_uploader(
        "Upload EOB images (one per page)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.write("Or paste directly from clipboard:")
    paste_result = paste_image_button("📋 Paste image")

    if paste_result.image_data is not None:
        img_b64 = image_to_base64(paste_result.image_data)
        if img_b64 not in st.session_state.pasted_images:
            st.session_state.pasted_images.append(img_b64)

    if st.session_state.pasted_images:
        st.write(f"**Pasted images ({len(st.session_state.pasted_images)}):**")
        for i, img_b64 in enumerate(st.session_state.pasted_images):
            col1, col2 = st.columns([4, 1])
            with col1:
                img_bytes = base64.b64decode(img_b64)
                st.image(img_bytes, width=300)
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.pasted_images.pop(i)
                    st.rerun()

    images_to_process = []
    if uploaded_files:
        for f in uploaded_files:
            images_to_process.append(base64.b64encode(f.read()).decode("utf-8"))
    images_to_process += st.session_state.pasted_images

    if st.button("Decode my EOB", key="image_btn", type="primary"):
        if not images_to_process:
            st.warning("Please upload or paste at least one image.")
        else:
            with st.spinner("Reading your EOB..."):
                try:
                    result = decode_images(images_to_process)
                    st.markdown("---")
                    st.markdown("### Here's what your EOB says:")
                    st.markdown(result)
                except Exception as e:
                    st.error(f"Something went wrong: {str(e)}")

with tab2:
    eob_text = st.text_area(
        "Paste your EOB text here",
        height=300,
        placeholder="Copy and paste the text from your EOB document here...",
        value=st.session_state.eob_text,
        key="text_input"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear", key="clear_text"):
            st.session_state.eob_text = ""
            st.rerun()
    with col2:
        if st.button("Decode my EOB", key="text_btn", type="primary"):
            if not eob_text.strip():
                st.warning("Please paste your EOB text first.")
            else:
                with st.spinner("Decoding your EOB..."):
                    try:
                        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": eob_text}
                            ]
                        )
                        result = response.choices[0].message.content
                        st.markdown("---")
                        st.markdown("### Here's what your EOB says:")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Something went wrong: {str(e)}")
