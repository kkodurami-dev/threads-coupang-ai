import streamlit as st
import random
import urllib.parse
import requests
import hmac
import hashlib
import json
import io
import os
import textwrap
from datetime import datetime
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
COUPANG_ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
COUPANG_SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)
COUPANG_DOMAIN = "https://api-gateway.coupang.com"

ITEMS = [
    {"keyword": "핸드폰 거치대", "pain": "영상 보다 손목 아픈 사람"},
    {"keyword": "수납 정리함", "pain": "방 정리가 자꾸 귀찮은 사람"},
    {"keyword": "미니 청소기", "pain": "책상 먼지 신경 쓰이는 사람"},
    {"keyword": "차량용 수납함", "pain": "차 안이 자꾸 지저분해지는 사람"},
    {"keyword": "욕실 정리템", "pain": "욕실 정리가 귀찮은 사람"},
    {"keyword": "책상 정리템", "pain": "물건 찾느라 흐름 끊기는 사람"},
    {"keyword": "주방 신박템", "pain": "요리보다 정리가 더 귀찮은 사람"},
    {"keyword": "무선 충전기", "pain": "충전선 찾느라 짜증나는 사람"},
    {"keyword": "LED 무드등", "pain": "방 분위기를 바꾸고 싶은 사람"},
    {"keyword": "캠핑 랜턴", "pain": "짐 줄이고 편하게 캠핑 가고 싶은 사람"},
]

def coupang_auth(method, path, query=""):
    now = datetime.utcnow().strftime("%y%m%dT%H%M%SZ")
    message = now + method + path + query

    signature = hmac.new(
        COUPANG_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return (
        f"CEA algorithm=HmacSHA256, "
        f"access-key={COUPANG_ACCESS_KEY}, "
        f"signed-date={now}, "
        f"signature={signature}"
    )

def search_coupang_product(keyword):
    encoded = urllib.parse.quote(keyword)
    path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query = f"?keyword={encoded}&limit=10"
    url = COUPANG_DOMAIN + path + query

    headers = {
        "Authorization": coupang_auth("GET", path, query),
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        products = data.get("data", {}).get("productData", [])

        if not products:
            return None

        return random.choice(products)

    except Exception:
        return None

def make_coupang_deeplink_from_product_url(product_url):
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    url = COUPANG_DOMAIN + path

    headers = {
        "Authorization": coupang_auth("POST", path),
        "Content-Type": "application/json"
    }

    payload = {
        "coupangUrls": [product_url]
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        data = res.json()

        if "data" in data and len(data["data"]) > 0:
            return data["data"][0].get("shortenUrl", product_url)

        return product_url

    except Exception:
        return product_url

def make_thread_text(keyword, pain):
    prompt = f"""
너는 한국 Threads에서 자연스럽게 확산되는 '일상 공감형 글'을 쓰는 작가다.

주제 물건: {keyword}
공감 대상: {pain}

목표:
제품을 파는 글이 아니라, 일상 속 작은 불편을 공감하게 만든다.
댓글의 제품 정보가 자연스럽게 궁금해지게 작성한다.

조건:
- 제품 추천 AI 느낌 금지
- 광고 느낌 금지
- 쇼핑몰 말투 금지
- 공감 + 궁금증 + 저장 욕구 포함
- 직접적인 구매 유도 금지
- 링크 언급 금지
- "사세요", "구매", "최저가", "인생템", "미쳤다", "대박" 금지
- 이모지는 0~1개
- 3~5문장
- 120~220자
- 마지막은 댓글을 유도하는 자연스러운 문장
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=220
        )
        return str(response.choices[0].message.content).strip()

    except Exception:
        return f"{pain}이라면 이런 작은 불편이 은근히 반복되죠. 별거 아닌데 매일 쌓이면 꽤 피곤합니다. 생활 동선 조금 편해지는 게 생각보다 크더라고요. 비슷한 거 느끼는 분 있나요?"

def get_korean_font(size):
    paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf"
    ]

    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)

    return ImageFont.load_default()

def download_product_image(url):
    try:
        res = requests.get(url, timeout=10)
        return Image.open(io.BytesIO(res.content)).convert("RGB")
    except Exception:
        return None

def make_card_news(keyword, thread_text):
    thread_text = str(thread_text)

    width, height = 1080, 1350
    img = Image.new("RGB", (width, height), (18, 19, 27))
    draw = ImageDraw.Draw(img)

    title_font = get_korean_font(70)
    body_font = get_korean_font(44)
    small_font = get_korean_font(30)

    draw.rounded_rectangle(
        (60, 60, 1020, 1290),
        radius=42,
        fill=(30, 32, 44)
    )

    draw.text(
        (95, 110),
        "생활 메모",
        fill=(200, 200, 210),
        font=small_font
    )

    draw.text(
        (95, 190),
        keyword,
        fill=(255, 255, 255),
        font=title_font
    )

    wrapped = textwrap.fill(thread_text, width=17)

    draw.text(
        (95, 360),
        wrapped,
        fill=(235, 235, 240),
        font=body_font,
        spacing=18
    )

    draw.text(
        (95, 1180),
        "저장해두면 좋은 일상 아이디어",
        fill=(150, 150, 160),
        font=small_font
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return img, buffer

st.set_page_config(
    page_title="Daily Life Threads Studio",
    page_icon="🔥",
    layout="centered"
)

st.title("🔥 Daily Life Threads Studio")
st.write("단일 상품 이미지 + 공감형 Threads 글 + 쿠팡파트너스 딥링크 + 카드뉴스 생성")

count = st.slider("자동 생성 개수", 1, 10, 3)

if st.button("🚀 오늘의 Threads 생성"):

    selected_items = random.sample(ITEMS, count)

    for item in selected_items:
        keyword = item["keyword"]
        pain = item["pain"]

        product = search_coupang_product(keyword)

        if product:
            product_name = product.get("productName", keyword)
            product_url = product.get("productUrl", "")
            product_img_url = product.get("productImage", "")

            if product_url:
                partner_url = make_coupang_deeplink_from_product_url(product_url)
            else:
                partner_url = "상품 URL을 가져오지 못했습니다."

        else:
            product_name = keyword
            product_url = ""
            product_img_url = ""
            partner_url = "쿠팡 상품 검색에 실패했습니다."

        thread_text = make_thread_text(keyword, pain)
        card_img, card_buffer = make_card_news(keyword, thread_text)

        st.divider()

        st.subheader(f"🔥 {keyword}")

        st.caption(f"선택된 단일 상품: {product_name}")

        product_img = download_product_image(product_img_url)

        if product_img:
            st.image(product_img, caption="단일 상품 이미지")
        else:
            st.info("상품 이미지를 불러오지 못했습니다. 카드뉴스만 생성됩니다.")

        st.text_area(
            "Threads 본문",
            thread_text,
            height=220
        )

        st.image(
            card_img,
            caption="저장용 카드뉴스"
        )

        st.download_button(
            label="📥 카드뉴스 다운로드",
            data=card_buffer,
            file_name=f"{keyword}_cardnews.png",
            mime="image/png"
        )

        st.text_area(
            "댓글용 쿠팡파트너스 단일 상품 딥링크",
            f"참고했던 제품은 여기예요👇\n{partner_url}\n\n※ 이 링크를 통해 구매 시 일정 수수료를 받을 수 있습니다.",
            height=130
        )

st.caption("Daily Life Threads Studio + Coupang Partners Deep Link")
