import streamlit as st
import logging
import atexit
from utils.content_generation import ContentGeneration
from utils.graphic.chart_generation import ChartGeneration
import utils.ppt_generation as ppt_gen
from utils.clear_tmp import clear_temp_files
import asyncio



logging.basicConfig(level=logging.INFO)

st.title("プレゼン資料生成📑")
st.caption("テキストを基づいてプレゼン資料を生成します。")


# User Input
L, R = st.columns(2)
with L:
    title = st.text_input("タイトル")
with R:
    num_of_slides = st.number_input("内容スライド数", min_value=1, max_value=20)
outline = st.text_area("テキストを入力:", height=300, max_chars=1000)
file_upload = st.file_uploader("テキストファイルをアップロード", accept_multiple_files=False)

# Generate PPT
if st.button("資料生成"):
    text = file_upload.read().decode() if file_upload else ""
    outline = outline + text
    
    with st.spinner("資料生成中..."):
        cg = ContentGeneration()
        content_generated = cg.generate_content(title=title, outline=outline, num_of_slides=num_of_slides)
        
        # Graphic generation
        gg = ChartGeneration()
        image_paths = []
        for i, slide in enumerate(content_generated.values()):
            content = slide['content']
            graphic_prompt = slide.get('graphic_prompt', '')
            image_path = asyncio.run(gg.run(content=content, chart_type='mindmap', custom_prompt=graphic_prompt, filename=f"slide_{i+1}"))
            image_paths.append(image_path)
        
        binary_ppt = ppt_gen.generate_ppt(title=title, content=content_generated, num_of_slides=num_of_slides, img_path=image_paths)
        
    # Download PPT
    download = st.download_button(label="資料ダウンロード", 
                                  data=binary_ppt, 
                                  file_name=f'{title}.pptx')   
    
# Clear tmp file on exit
atexit.register(clear_temp_files)
