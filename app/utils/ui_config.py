import streamlit as st
import os
import pandas as pd

def configure_sidebar():
    st.sidebar.write("## モデルの選択")
    models = ["gpt-4o","gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
    selected_model = st.sidebar.selectbox(
        'モデルを選択してください',
        options=models,
        index=0
    )

    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=1.0)

    use_cache = st.sidebar.checkbox("Use cache", value=True)
    uploaded_file_path = None
    '''
    ファイルのアップロードに関して
    
    '''

    file_names = [file[0] for file in st.session_state['uploaded_file']]
    
    if file_names:
        upload_own_data = st.sidebar.checkbox("Upload your own data")
        selected_dataset_label = st.sidebar.selectbox(
            'Choose a dataset',
            options=file_names,
            index=0
        )
        uploaded_file_path = next((file[1] for file in st.session_state['uploaded_file'] if file[0] == selected_dataset_label), None)
        if upload_own_data:
            uploaded_file = st.sidebar.file_uploader("Choose a CSV or JSON file", type=["csv", "json"])  
            if uploaded_file is not None:
                file_name, file_extension = os.path.splitext(uploaded_file.name)

                # Load the data depending on the file type
                if file_extension.lower() == ".csv":
                    data = pd.read_csv(uploaded_file)
                elif file_extension.lower() == ".json":
                    data = pd.read_json(uploaded_file)

                # Save the data using the original file name in the data dir
                uploaded_file_path = os.path.join("data", uploaded_file.name)
                data.to_csv(uploaded_file_path, index=False) 
                st.session_state['uploaded_file'].append((file_name, uploaded_file_path))

    else:
        uploaded_file = st.sidebar.file_uploader("Choose a CSV or JSON file", type=["csv", "json"])  
        if uploaded_file is not None:
            file_name, file_extension = os.path.splitext(uploaded_file.name)

            # Load the data depending on the file type
            if file_extension.lower() == ".csv":
                data = pd.read_csv(uploaded_file)
            elif file_extension.lower() == ".json":
                data = pd.read_json(uploaded_file)

            # Save the data using the original file name in the data dir
            uploaded_file_path = os.path.join("data", uploaded_file.name)
            data.to_csv(uploaded_file_path, index=False)   
            st.session_state['uploaded_file'].append((file_name, uploaded_file_path))

        else:
            st.sidebar.warning("ファイルがアップロードされていません。データセットを選択するかファイルをアップロードしてください。")
    # Handle dataset selection and upload
    st.sidebar.write("## データの要約")
    st.sidebar.write("### 要約方法の選択")
    
    summarization_methods = [
        {"label": "llm",
         "description":
         "LLMを使用してデフォルトの要約に注釈を付けて生成（データセットのセマンティックタイプや説明などの詳細を追加）"},
        {"label": "default",
         "description": 
         "データセットの列統計と列名を要約として使用"},
        {"label": "columns", 
         "description": 
         "データセットの列名を要約として使用"}]
    
    selected_method_label = st.sidebar.selectbox(
        '要約方法を選択してください',
        options=[method["label"] for method in summarization_methods],
        index=0
    )

    selected_method = summarization_methods[[
        method["label"] for method in summarization_methods].index(selected_method_label)]["label"]

    selected_summary_method_description = summarization_methods[[
        method["label"] for method in summarization_methods].index(selected_method_label)]["description"]

    if selected_method:
        st.sidebar.markdown(
            f"<span style='font-size: 12px;'> {selected_summary_method_description} </span>",
            unsafe_allow_html=True)
    

    st.sidebar.write("## グラフ作成")
    visualization_libraries = ["seaborn", "matplotlib", "plotly"]
    selected_library = st.sidebar.selectbox(
                    'グラフ作成のライブラリを選択',
                    options=visualization_libraries,
                    index=0)
    
    num_visualizations = st.sidebar.slider(
                        "Number of visualizations to generate",
                        min_value=1,
                        max_value=10,
                        value=2)

    return selected_model, temperature, use_cache, uploaded_file_path,selected_method,selected_library,num_visualizations