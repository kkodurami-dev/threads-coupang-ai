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

KEYWORDS = [
    "핸드폰 거치대", "자취 꿀템", "차량용 꿀템", "캠핑 꿀템",
    "책상 정리템", "욕실 꿀템", "주방 신박템", "수납 정리함",
    "미니 청소기", "LED 무드등", "무선 충전기", "차박 꿀템"
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

def make_coupang_search_url(keyword):
    encoded = urllib.parse.quote(keyword)
    return f"https://www.coupang.com/np/search?q={encoded}"

def make_coupang_deeplink(coupang_url):
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    url = COUPANG_DOMAIN + path

    headers = {
        "Authorization": coupang_auth("POST", path),
        "Content-Type": "application/json"
    }

    payload = {
        "coupangUrls": [coupang_url]
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        data = res.json()

        if "data" in data and len(data["data"]) > 0:
            return data["data"][0].get("shortenUrl", coupang_url)

        return coupang_url

    except Exception:
        return coupang_url

def make_thread_text(keyword):

st.write(thread_text)

    prompt = f"""
    당신은 Threads 바이럴 콘텐츠 전문가다.

    광고 느낌 없이
    실제 사용 후기처럼 자연스럽게 작성하라.

    조건:
    - 2~3문장
    - 공감형 말투
    - 저장하고 싶은 느낌
    - 광고 티 금지
    - 과장 금지
    - 짧고 가독성 좋게
    - Threads 스타일

    제품:
    {keyword}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8,
        max_tokens=120
    )

    text = response.choices[0].message.content

    return str(text).strip()

def get_korean_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf"
    ]

    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    font_url = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
    font_path = "NotoSansKR.ttf"

    try:
        if not os.path.exists(font_path):
            r = requests.get(font_url, timeout=10)
            with open(font_path, "wb") as f:
                f.write(r.content)
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def make_card_news(keyword, thread_text):
    
    thread_text = str(thread_text)
    
    width, height = 1080, 1350

    img = Image.new("RGB", (width, height), (16, 17, 24))

    draw = ImageDraw.Draw(img)

    title_font = get_korean_font(72)
    body_font = get_korean_font(48)
    small_font = get_korean_font(34)

    draw.rounded_rectangle(
        (50, 50, 1030, 1300),
        radius=42,
        fill=(28, 30, 42)
    )

    draw.text(
        (90, 100),
        "생활 메모",
        fill=(210, 210, 210),
        font=small_font
    )

    draw.text(
        (90, 180),
        keyword,
        fill=(255, 255, 255),
        font=title_font
    )

    wrapped = textwrap.fill(thread_text, width=18)

    draw.text(
        (90, 360),
        wrapped,
        fill=(238, 238, 238),
        font=body_font,
        spacing=18
    )

    draw.text(
        (90, 1180),
        "나중에 참고하기 좋은 생활 아이디어",
        fill=(170, 170, 180),
        font=small_font
    )

    buffer = io.BytesIO()

    img.save(buffer, format="PNG")

    buffer.seek(0)

    return img, buffer

st.set_page_config(page_title="Threads AI 수익 자동화", page_icon="🔥", layout="centered")

st.title("🔥 Threads AI 수익 자동화")
st.write("광고티 없이 Threads 최적화 글 + 쿠팡파트너스 딥링크 + 카드뉴스 생성")

count = st.slider("자동 생성 개수", 1, 10, 3)

if st.button("🚀 오늘의 Threads 자동 생성"):
    selected_keywords = random.sample(KEYWORDS, count)

    for keyword in selected_keywords:
        st.divider()

        normal_url = make_coupang_search_url(keyword)
        partner_url = make_coupang_deeplink(normal_url)

        thread_text = make_thread_text(keyword)
        card_img, card_buffer = make_card_news(keyword, thread_text)

        st.subheader(f"🔥 {keyword}")

        st.text_area("Threads 본문", thread_text, height=160)

        st.text_area(
            "댓글용 쿠팡파트너스 링크",
            f"🔗 제품 정보\n{partner_url}\n\n※ 이 링크를 통해 구매 시 일정 수수료를 받을 수 있습니다.",
            height=140
        )

        st.image(card_img)

        st.download_button(
            label="📥 카드뉴스 다운로드",
            data=card_buffer,
            file_name=f"{keyword}_cardnews.png",
            mime="image/png"
        )

st.caption("Threads + 쿠팡파트너스 자동화 시스템")
