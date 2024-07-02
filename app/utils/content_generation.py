import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import logging
import json
import time
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
logging.basicConfig(level=logging.INFO)

class ContentGeneration:
    def __init__(self) -> None:
        self.example ="""
        "slide1": {
            "title": "生成型AI(ジェネラティブAI)とは",
            "content": [
                "生成型AIは学習データから新しいコンテンツを生成する人工知能の一種です。",
                "自然言語処理、画像生成、音声合成など多岐にわたる応用が可能です。",
                "代表的な技術にはGAN(Generative Adversarial Networks)や変分オートエンコーダーがあります。",
                "データの内在するパターンを理解し、それに基づいて新しいデータを創出します。"
            ],
            "graphic_prompt": "AIのシンボル(人工知能の脳)がデジタル情報(0と1)を吸収している様子"
            },
        "slide2": {
            "title": "ジェネラティブAIの応用例",
            "content": [
                "テキスト：チャットボット、物語や記事の自動生成、プログラムコードの作成補助。",
                "画像：アート作品の生成、写真リアルなイメージの作成、顔写真の年齢変化シミュレーション。",
                "音声：バーチャルアシスタントの応答音声生成、オーディオブック読み上げ、音楽作成。",
                "予測分析：商品需要予測や金融市場予測などビジネスでの意思決定支援。"
            ],
            "graphic_prompt": "様々な応用分野（記事、ゲーム、音楽、教育）が回転する歯車として描かれるイメージ"
        }
        """
        
    def generate_content(self, title: str, outline: str, num_of_slides: int) -> dict:
        """タイトルとアウトラインで内容を生成

        Args:
            title (str): タイトル,
            outline (str): アウトライン

        Returns: 
            dict: 生成された内容

        """ 
        
        start_time = time.time()

        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {
                    "role": "system",
                    "content" : f"You will act as a business presenter that speaks and writes fluently in Japanese.\
                        I will give you the title and materials, and you will summarize it into a easy to understand presentation.\
                        The presentation should be written in Japanese. Response should be in JSON format like {self.example}."
                },
                {
                    "role": "user",
                    "content": f"You will provide content for a presentation on {title} based on text provided.\
                        Text: {outline}. Split the text into {num_of_slides} slides. Summarize into 2 to 5 bullet points for each slide.\
                        Do not generate any escape sequence.\
                        Suggest a graphic to help provide a visual to reinforce each slide. Label the graphic as a prompt to be used with DALL-E 3 to generate the graphic.\
                        "
                }
            ],
            temperature=0.8,
            response_format={"type": "json_object"}
        )

        escape_characters = r'[\n\r\t\f\v]'
        content_generated = response.choices[0].message.content
        cleaned_content = json.loads(re.sub(escape_characters, '', content_generated))
        
        time_taken = time.time() - start_time
        logging.info(f"Response: {cleaned_content}")
        logging.info(f"Finish Reason: {response.choices[0].finish_reason}")
        logging.info(f"Time Taken: {time_taken}")

        if response.choices[0].finish_reason != "stop":
            raise Exception(f"Generation not completed. Finish reason: {response.choices[0].finish_reason}")

        return cleaned_content


if __name__ == "__main__":
    outline = "生成型AIは学習データから新しいコンテンツを生成する人工知能の一種です."
    cg = ContentGeneration()
    content = cg.generate_content(title="generative AI", num_of_slides=20, outline=outline)