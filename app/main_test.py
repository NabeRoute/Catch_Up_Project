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

def main():
    st.title("プレゼン資料生成📑")
    st.caption("テキストに基づいてプレゼン資料を生成します。")

    # サイドバーの設定
    with st.sidebar:
        st.header("オプション設定")
        selected_model, temperature, use_cache = configure_sidebar()
        
        st.header("データ表示機能")
        if st.checkbox("データ表示を追加"):
            show_data_visualization_options()

    # メイン画面
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("1. プレゼンテーションの詳細を入力")
        title = st.text_input("タイトル")
        num_of_slides = st.number_input("内容スライド数", min_value=1, max_value=20)
        outline = st.text_area("テキストを入力:", height=300, max_chars=1000)
        
        st.subheader("2. ファイルをアップロード（オプション）")
        file_upload = st.file_uploader("テキストファイルをアップロード", accept_multiple_files=False)

    with col2:
        st.subheader("3. 資料を生成")
        if st.button("資料生成"):
            generate_presentation(title, num_of_slides, outline, file_upload)

def show_data_visualization_options():
    st.subheader("データ表示設定")
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")
    if uploaded_file:
        st.success("ファイルがアップロードされました。")
        st.subheader("データの要約方法")
        summary_method = st.selectbox(
            "要約方法を選択",
            ["LLM (AI分析)", "Default (基本統計)", "Columns (列名のみ)"],
            format_func=lambda x: x.split(" ")[0]
        )
        st.info(summary_method.split(" ")[1])
        
        if st.button("グラフを生成"):
            # グラフ生成のロジックをここに実装
            st.success("グラフが生成されました。")

def generate_presentation(title, num_of_slides, outline, file_upload):
    with st.spinner("資料生成中..."):
        # 既存の資料生成ロジックをここに実装
        st.success("資料が生成されました。")
        # ダウンロードボタンの表示

if __name__ == "__main__":
    main()