import streamlit as st
import logging
import atexit
import asyncio
import base64
import os
from utils.content_generation import ContentGeneration
from utils.graphic.chart_generation import ChartGeneration
import utils.ppt_generation as ppt_gen
from utils.clear_tmp import clear_temp_files
from utils.graph_gen import GraphGeneration, VisualizationProcessor, PPTXGenerator, load_settings
from utils.ui_config import configure_sidebar
from utils.src.lida import Manager, llm
from utils.src.lida.datamodel import Goal
from PIL import Image
from io import BytesIO


logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")

# Initialize components
os.makedirs("data", exist_ok=True)
openai_key = load_settings('.env')
vp = VisualizationProcessor()
ppt = PPTXGenerator()
gg = GraphGeneration(openai_key)

def get_openai_key(openai_key=None):
    if openai_key is None:
        openai_key = st.sidebar.text_input("OpenAI API keyを入力してください:")
        if openai_key:
            display_key = openai_key[:2] + "*" * (len(openai_key) - 5) + openai_key[-3:]
            st.sidebar.write(f"Current key: {display_key}")
    else:
        display_key = openai_key[:2] + "*" * (len(openai_key) - 5) + openai_key[-3:]
        st.sidebar.write(f"OpenAI API key loaded from environment variable: {display_key}")
    return openai_key

def initialize_session_state(defaults):
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def main():
    #global gg
    st.title("プレゼン資料生成📑")
    st.caption("テキストを基づいてプレゼン資料を生成します。")

    # Sidebar
    get_openai_key(openai_key)
    initialize_session_state({
        'uploaded_file': [],
        'summary': None,
        'goals': [],
        'selected_goal': None,
        'visualizations': None,
        'selected_viz_title': None,
        'viz_titles': [],
        'goal_generation_mode': None,
        'selected_viz': None,
        'generated_graphs': []
    })

    if 'api_key' not in st.session_state or st.session_state.api_key != openai_key:
        st.session_state.api_key = openai_key
        st.session_state.lida = Manager(text_gen=llm("openai", api_key=openai_key))

    gg = GraphGeneration(openai_key)

    selected_model, temperature, use_cache, uploaded_file_path, selected_method, selected_library, num_visualizations = configure_sidebar()

    # Graph generation in sidebar
    st.sidebar.header("グラフ生成")
    if st.sidebar.button('データの要約を生成'):
        with st.spinner('データを要約しています...'):
            st.session_state['summary'] = gg.generate_summary(
                manager=st.session_state.lida,
                uploaded_file_path=uploaded_file_path,
                summary_method=selected_method,
                model=selected_model,
                temperature=temperature,
                use_cache=use_cache
            )

    if st.session_state.summary:
        st.sidebar.write("## ゴール設定")
        st.session_state['goal_generation_mode'] = st.sidebar.radio(
            "ゴール生成か、手動入力のどちらかを選んでください",
            ('Generate', 'Input Manually')
        )

        if st.session_state['goal_generation_mode'] == 'Generate':
            if st.sidebar.button('ゴールを生成'):
                with st.spinner('ゴールを生成しています...'):
                    st.session_state['goals'] = gg.generate_goals(
                        manager=st.session_state.lida,
                        summary=st.session_state['summary'],
                        num_goals=3,
                        model=selected_model,
                        temperature=temperature,
                        use_cache=use_cache
                    )
                    goal_options = [goal.question for goal in st.session_state['goals']]
                    st.session_state['selected_goal'] = st.sidebar.selectbox("以下からゴールを選択してください", goal_options)
        else:
            if st.session_state['selected_goal'] is None:
                user_goal = st.sidebar.text_input("あなたのゴールを記述してください")
                if user_goal:
                    st.session_state['selected_goal'] = Goal(question=user_goal, visualization=user_goal, rationale="").question

        if st.session_state['selected_goal'] is not None:
            st.sidebar.write("選択されたゴール:")
            st.sidebar.write(st.session_state['selected_goal'])
            if st.sidebar.button('グラフを生成'):
                with st.spinner('グラフを生成しています...'):
                    st.session_state['visualizations'] = gg.generate_visualizations(
                        manager=st.session_state.lida,
                        summary=st.session_state.summary,
                        goal=st.session_state.selected_goal,
                        model=selected_model,
                        num_visualizations=num_visualizations,
                        temperature=temperature,
                        use_cache=use_cache,
                        library=selected_library
                    )

        if st.session_state['visualizations'] is not None:
            file_paths = vp.render_visualizations(st.session_state['visualizations'])
            st.session_state['viz_titles'] = [f'Visualization {i+1}' for i in range(len(st.session_state['visualizations']))]
            st.session_state['selected_viz_title'] = st.sidebar.selectbox(
                '選択して詳細表示',
                options=st.session_state['viz_titles']
            )
            st.session_state['selected_viz'], selected_index = vp.display_selected_visualization(
                viz_titles=st.session_state['viz_titles'],
                visualizations=st.session_state['visualizations'],
                selected_title=st.session_state['selected_viz_title']
            )
            
            if selected_index is not None:
                base64_image = encode_image(file_paths[selected_index])
                image_data = base64.b64decode(base64_image)
                image = Image.open(BytesIO(image_data))
                st.sidebar.image(image, use_column_width=True)
            
            if st.sidebar.button('グラフを決定'):
                if 'selected_viz' in st.session_state and 'selected_viz_title' in st.session_state:
                    st.session_state['generated_graphs'].append({
                        'title': st.session_state['selected_viz_title'],
                        'viz': st.session_state['selected_viz'],
                        'base64_image': base64_image
                    })
                    st.sidebar.success(f"{st.session_state['selected_viz_title']} が追加されました。")
                else:
                    st.sidebar.error("グラフを生成して選択してください。")

    # Main content area
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("タイトル")
        num_of_slides = st.number_input("内容スライド数", min_value=1, max_value=20)
        outline = st.text_area("テキストを入力:", height=300, max_chars=1000)
        file_upload = st.file_uploader("テキストファイルをアップロード", accept_multiple_files=False)

    with col2:
        st.write("## 生成されたグラフ")
        for graph in st.session_state['generated_graphs']:
            st.write(f"### {graph['title']}")


            # Base64エンコードされた画像をデコードしてPIL Imageオブジェクトに変換
            image_data = base64.b64decode(graph['base64_image'])
            image = Image.open(BytesIO(image_data))
        
            # PIL ImageオブジェクトをStreamlitで表示
            st.image(image, use_column_width=True)

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
            
            binary_ppt = ppt_gen.generate_ppt(
                title=title, 
                content=content_generated, 
                num_of_slides=len(content_generated), 
                img_path=image_paths,
                generated_graphs=st.session_state['generated_graphs']
                )   
           
        # Download PPT
        download = st.download_button(label="資料ダウンロード", 
                                      data=binary_ppt, 
                                      file_name=f'{title}.pptx')   

# Clear tmp file on exit
atexit.register(clear_temp_files)

if __name__ == "__main__":
    main()
