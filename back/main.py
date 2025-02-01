from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
import openai
import os
from dotenv import load_dotenv
import time
# from starlette.middleware.timeout import TimeoutMiddleware
from middleware.timeout import CustomTimeoutMiddleware
from starlette.responses import JSONResponse
from starlette.status import HTTP_408_REQUEST_TIMEOUT
from fastapi.middleware.cors import CORSMiddleware # 追加

import json

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAI APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# リクエスト処理全体にタイムアウトを設定するミドルウェアを追加
app.add_middleware(CustomTimeoutMiddleware, timeout=300)

@app.middleware("http")
async def timeout_exception_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except TimeoutError:
        return JSONResponse(
            status_code=HTTP_408_REQUEST_TIMEOUT,
            content={"detail": "Request timeout"}
        )

# CORS 設定を追加
origins = [
    "http://localhost:3000",
    "http://localhost:3001",  # フロントエンドのオリジン
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # すべてのメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# リクエストボディのモデル
class ProductInfo(BaseModel):
    product_name: str
    product_description: str

# レスポンスボディのモデル
class ComicResponse(BaseModel):
    image_urls: List[str]
    texts: List[str]

# GPT APIを使って4コマ漫画のストーリーを作成する関数
def generate_comic_story(product_name: str, product_description: str) -> str:
    prompt = f"「{product_name}」という商品を題材にした4コマ漫画を作成したいので起承転結で4コマの流れを作成して欲しい。商品説明：{product_description}。また、人物が出てくる場合、詳細にその人物の特徴を記載してください。"
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            # {"role": "system", "content": "あなたは、商品情報をもとに4コマ漫画のストーリーを作成するプロです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# DALL-E APIを使って画像を生成する関数（吹き出しなし）
def generate_image_without_speech_bubble(prompt: str, panel_number: int) -> str:
    panel_prompt = (
        f"以下はカラーマンガの全体の流れです：\n{prompt}\n\n"
        f"上記の流れから、{panel_number}コマ目に該当するシーンのみを1枚の画像として生成してください。"
        "画像には複数のコマを含めず、あくまでそのシーンのみを１つ漫画風に描写してください。"
        "また、吹き出しは一切入れないでください。"
    )
    response = openai.images.generate(
        model="dall-e-3",
        prompt=panel_prompt,
        n=1,
        size="1024x1024"
    )
    return response.data[0].url


# GPT APIを使って画像とテキストからセリフを抽出する関数
def extract_text_from_image_and_story(story: str, image_urls: List[str], panel_number: int) -> str:
    # GPT に必ず JSON を返すように指示するプロンプト
    prompt = (
        f"4コマ漫画のストーリー「{story}」の{panel_number}コマ目の画像({image_urls[panel_number-1]})が生成されました。\n"
        "この画像にふさわしいセリフを、以下の JSON 形式で返してください:\n\n"
        "{\n"
        '    "panel": <数字>,\n'
        '    "dialogue": "<セリフ>"\n'
        "}\n\n"
        "※必ず純粋な JSON を返してください。出力には Markdown のコードブロック（```）や余計な文章を含めないでください。必ず「JSON」という文字列も含めてください。"
    )
    
    messages = [
        {
            "role": "system",
            "content": (
                "あなたは、必ず純粋な JSON を返すアシスタントです。"
                "出力は有効な JSON オブジェクトであり、コードブロックや追加の文章は含めないでください。"
                "また、出力には必ず 'JSON' という文字列を含めること。"
            )
        },
        {"role": "user", "content": prompt}
    ]
    
    # JSON モードを有効にするため、可能であれば response_format を指定する
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}  # ※API がサポートしていれば有効になります
        )
    except Exception as e:
        # response_format パラメータがエラーになる場合は、パラメータなしで再試行
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
    
    text_response = response.choices[0].message.content.strip()
    
    # もしコードブロックが含まれている場合は除去
    if text_response.startswith("```") and text_response.endswith("```"):
        text_response = text_response.strip("```").strip()
    
    try:
        parsed = json.loads(text_response)
        dialogue = parsed.get("dialogue", "").strip()
        return dialogue
    except json.JSONDecodeError:
        # JSON になっていない場合、デバッグ用に全文を返すか、もしくは再試行ロジックを検討する
        return text_response


@app.post("/generate_comic", response_model=ComicResponse)
async def generate_comic(product_info: ProductInfo):
    try:
        # 1. 4コマ漫画のストーリーを生成
        story = generate_comic_story(product_info.product_name, product_info.product_description)

        # 各コマのプロンプトをストーリーから抽出（簡略化）
        panel_prompts = story.split("\n")
        panel_prompts = [prompt for prompt in panel_prompts if prompt]
        if len(panel_prompts) != 4:
          panel_prompts = [story]*4

        # 2. 1コマ目の画像を生成
        image_url1 = generate_image_without_speech_bubble(panel_prompts[0], 1)
        time.sleep(1)
        print('panel_prompts[0]: ', panel_prompts[0])

        # 3. 2コマ目の画像を生成 (代替案: プロンプトを調整)
        image_url2 = generate_image_without_speech_bubble(panel_prompts[1], 2)
        time.sleep(1)
        print('panel_prompts[1]: ', panel_prompts[1])
        # 4. 3コマ目の画像を生成 (代替案: プロンプトを調整)
        image_url3 = generate_image_without_speech_bubble(panel_prompts[2], 3)
        time.sleep(1)
        print('panel_prompts[2]: ', panel_prompts[2])
        # 5. 4コマ目の画像を生成 (代替案: プロンプトを調整)
        image_url4 = generate_image_without_speech_bubble(panel_prompts[3], 4)
        time.sleep(1)
        print('panel_prompts[3]: ', panel_prompts[3])

        image_urls = [image_url1, image_url2, image_url3, image_url4]
        # image_urls = [image_url1, image_url1, image_url1, image_url1]
        # 6. 各コマのセリフを取得
        texts = []
        for i in range(4):
            text = extract_text_from_image_and_story(story, image_urls, i + 1)
            texts.append(text)

            # time.sleep(1)

        return ComicResponse(image_urls=image_urls, texts=texts)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))