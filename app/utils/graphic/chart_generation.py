import openai
import logging
import os
import subprocess
import time
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio
from PIL import Image

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI()
logging.basicConfig(level=logging.INFO)

class ChartGeneration:
    def __init__(self) -> None:
        self.example = {
            "er_diagram": """erDiagram
                                CUSTOMER }|..|{ DELIVERY-ADDRESS : has
                                CUSTOMER ||--o{ ORDER : places
                                CUSTOMER ||--o{ INVOICE : "liable for"
                                DELIVERY-ADDRESS ||--o{ ORDER : receives
                                INVOICE ||--|{ ORDER : covers
                                ORDER ||--|{ ORDER-ITEM : includes
                                PRODUCT-CATEGORY ||--|{ PRODUCT : contains
                                PRODUCT ||--o{ ORDER-ITEM : "ordered in"
                                """,
            "flowchart": """flowchart TD
                                Start --> Stop
                            """,
            "mindmap": """mindmap
                            root((mindmap))
                              Origins
                                Long history
                                ::icon(fa fa-book)
                                Popularisation
                                  British popular psychology author Tony Buzan
                              Research
                                On effectivness<br/>and features
                                On Automatic creation
                                  Uses
                                      Creative techniques
                                      Strategic planning
                                      Argument mapping
                              Tools
                                Pen and paper
                                Mermaid""",
            "timeline": """timeline
                                title History of Social Media Platform
                                2002 : LinkedIn
                                2004 : Facebook
                                     : Google
                                2005 : Youtube
                                2006 : Twitter"""
        }
    
    async def generate_chart(self, content: list, chart_type: str, custom_prompt: str) -> str:
        """タイトルと内容からチャートを生成

        Args:
            content (list): 内容
            graphic_prompt (str): プロンプト

        Returns: 
            str: 生成されたチャートのmermaid.jsコード

        """ 
        
        start = time.time()
        
        # Create Chart
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content" : f"You will act as a engineer fluent in making chart, mindmaps, timelines, ER diagrams etc. in mermaid.js.\
                        I will give you the content, type of chart, and a customization prompt. You will generate a mermaid.js chart that follow the customization prompt.\
                        Example: {self.example[chart_type]}. Make necesssary changes based on customization prompt. Do not use theme as it is not supported with CLI.\
                        Only return the mermaid.js code. "
                },
                {
                    "role": "user",
                    "content" : f"Content: {content}\
                        Type of chart: {chart_type}\
                        Customization prompt: {custom_prompt}."
                }
            ],
            temperature=0.8,
        )
        
        chart_code = response.choices[0].message.content
        cleaned_code = chart_code.replace("```mermaid", "").replace("```", "").strip()
        logging.info(f"Time Taken: {time.time() - start}")
        logging.info(f"Mermaid.js Generated: {cleaned_code}")
        
        return cleaned_code
    
    def save_chart(self, chart_code: str, filename: str) -> None:
        """mermaid.jsコードをファイルに保存

        Args:
            chart_code (str): mermaid.jsコード
            filename (str): ファイル名

        """ 
        
        tempdir = "./tmp"
        os.makedirs(tempdir, exist_ok=True)
        file_path = os.path.join(tempdir, f"{filename}.mmd")
        with open(file_path, "w") as file:
            file.write(chart_code)
        image_path = os.path.join(tempdir, f"{filename}.png")
        try:
            subprocess.run(["mmdc", "-i", file_path, "-o", image_path, "-b", "transparent"], check=True, capture_output=True)
            logging.info(f"Chart saved to {image_path}")
        
        except subprocess.CalledProcessError as e:
            raise Exception(e.stderr.decode("utf-8"))
        
        return image_path
    
    async def fix_code(self, code: str, error: str) -> str:
        """エラーを修正

        Args:
            code (str): コード
            error (str): エラー

        Returns:
            str: 修正されたコード

        """ 
        
        logging.info(f"Fixing code. Error: {error}")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a software engineer who is fluent in fixing mermaid.js code errors. I will give you a code snippet and an error message.\
                        You will fix the code to remove the error. Only return the fixed mermaid.js code"
                },
                {
                    "role": "user",
                    "content": f"#Code: {code}"
                }
            ],
        )
        
        fixed_code = response.choices[0].message.content
        cleaned_code = fixed_code.replace("```mermaid", "").replace("```", "").strip()
        logging.info(f"Fixed Code: {cleaned_code}")
        
        return cleaned_code
    
    
    #local test run
    async def run(self, content: list, chart_type: str, custom_prompt:str, filename: str) -> None:
        try_count = 0
        error = ""
        while try_count < 3:
            try:
                if try_count == 0:
                    chart_code = await self.generate_chart(content=content, chart_type=chart_type, custom_prompt=custom_prompt)
                else:
                    chart_code = await self.fix_code(code=chart_code, error=error)
    
                image_path = self.save_chart(chart_code=chart_code, filename=filename)
                
                return image_path
        
            except Exception as e:
                error = str(e)
                try_count += 1
                continue
                
        else:
            logging.error("Failed to generate chart after 3 attempts.")
            return None
               
    
if __name__ == "__main__":
    content = ["プロジェクト管理は、スケジュールの設定、リソースの割り当て、コストの管理、リスクの評価、品質の保証、そして効果的なコミュニケーションに重点を置いています。各プロジェクトの成功は、これらの要素がどれだけうまく統合され管理されるかにかかっています。スケジュール管理では、全ての活動が計画通りに進むように時間を配置します。リソース管理には、必要な人材と物資を適切に配分し、コスト管理を通じて予算内でプロジェクトを完了させることが含まれます。リスク管理では、潜在的な問題を予測し対策を講じ、品質管理はプロダクトが顧客の期待を満たすことを保証します。そして、コミュニケーションはチーム内外のステークホルダーとの明確な情報交換を確実に行うために不可欠です。これらの管理技術は、プロジェクトをスムーズに進行させ、目標達成を助けるために極めて重要です。"]
    chart_type = 'mindmap'
    custom_prompt = ''
    chart_gen = ChartGeneration()
    asyncio.run(chart_gen.run(content=content, chart_type=chart_type, custom_prompt=custom_prompt, filename="chart"))
    