from graph_gen import load_settings, GraphGeneration, VisualizationProcessor, PPTXGenerator
from ui_config import configure_sidebar
from src.lida import Manager, llm
from src.lida.datamodel import Goal
import streamlit as st
import base64
import os

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
        'selected_viz': None
    })

    if 'api_key' not in st.session_state or st.session_state.api_key != openai_key:
        st.session_state.api_key = openai_key
        st.session_state.lida = Manager(text_gen=llm("openai", api_key=openai_key)) 
    
    if st.session_state.api_key:
        selected_model, temperature, use_cache, uploaded_file_path, selected_method, selected_library, num_visualizations = configure_sidebar()
        if uploaded_file_path is None:
            st.info("左のサイドバーから、データセットをアップロードしてください。")
    
    if uploaded_file_path and selected_method:
        if st.button('データの要約を生成'):
            with st.spinner('データを要約しています...'):
                st.session_state['summary'] = gg.generate_summary(
                    manager=st.session_state.lida,
                    uploaded_file_path=uploaded_file_path,
                    summary_method=selected_method,
                    model=selected_model,
                    temperature=temperature,
                    use_cache=use_cache
                )
                print(st.session_state['summary'])
    
    if st.session_state.summary:
        summary = st.session_state.summary
        if 'dataset_description' in summary:
            st.write(f"## 要約")
            st.write(summary["dataset_description"])
            if "fields" in summary:
                nfields_df = vp.process_summary(summary)
                st.write(nfields_df)
            else:
                st.error('要約に失敗しました。')
        else:
            st.error('要約に失敗しました。')

        st.write(f"## ゴール設定")
        st.session_state['goal_generation_mode'] = st.radio(
            "ゴール生成か、手動入力のどちらかを選んでください",
            ('Generate', 'Input Manually')
        )

        if st.session_state['goal_generation_mode'] == 'Generate':
            # ゴールを生成する場合
            if st.button('ゴールを生成'):
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
                    st.session_state['selected_goal'] = st.selectbox("以下からゴールを選択してください", goal_options)
        else:
            # 手動入力の場合
            if st.session_state['selected_goal'] is None:
                user_goal = st.text_input("あなたのゴールを記述してください")
                if user_goal:
                    st.session_state['selected_goal'] = Goal(question=user_goal, visualization=user_goal, rationale="").question
        
        if st.session_state['selected_goal'] is not None:
            st.write("選択されたゴール:")
            st.write(st.session_state['selected_goal'])
            if st.button('グラフを生成'):
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
            st.write("## グラフ作成")
            file_paths = vp.render_visualizations(st.session_state['visualizations'])
            st.session_state['viz_titles'] = [f'Visualization {i+1}' for i in range(len(st.session_state['visualizations']))]
            st.selectbox(
                '選択して詳細表示',
                index=0,
                options=st.session_state['viz_titles'],
                key="selected_viz_title"
            )
            st.session_state['selected_viz'], selected_index = vp.display_selected_visualization(
                viz_titles=st.session_state['viz_titles'],
                visualizations=st.session_state['visualizations'],
                selected_title=st.session_state['selected_viz_title']
            )
            if selected_index is not None:
                base64_image = encode_image(file_paths[selected_index])

        if st.session_state['selected_viz'] is not None:
            decide_button = st.button('グラフを決定')
            st.session_state.instructions = st.text_input("どのように編集するか記述してください")
            edit_button = st.button('グラフを編集')

            if decide_button:
                st.write("グラフが決定されました。")
                st.session_state['decided_viz'] = st.session_state['selected_viz']

            if edit_button:
                st.write("## グラフ編集")
                edited_chart = gg.edit_chart(
                    manager=st.session_state.lida,
                    summary=st.session_state.summary,
                    model=selected_model,
                    temperature=temperature,
                    use_cache=use_cache,
                    code=st.session_state['selected_viz'].code,
                    instructions=st.session_state.instructions,
                    library=selected_library
                )
                st.session_state['edited_viz'] = vp.display_selected_visualization(
                    viz_titles=st.session_state['viz_titles'],
                    visualizations=edited_chart,
                    selected_title=st.session_state['selected_viz_title']
                )[0]

        if 'decided_viz' in st.session_state or 'edited_viz' in st.session_state:
            if st.button("保存"):
                descriptions = gg.describe_features(
                    manager=st.session_state.lida,
                    summary=st.session_state.summary,
                    goal=st.session_state.selected_goal,
                    base64_image=base64_image
                )
                print(descriptions)
                print(type(descriptions))
                image = st.session_state['edited_viz'] if 'edited_viz' in st.session_state else st.session_state['decided_viz']
                pptx_file = ppt.save_to_pptx(descriptions, image)
                st.download_button(
                    label="Download PowerPoint",
                    data=pptx_file,
                    file_name="presentation.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )

if __name__ == "__main__":
    main()