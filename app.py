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

# =========================
# API KEYS
# =========================

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
COUPANG_ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
COUPANG_SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

COUPANG_DOMAIN = "https://api-gateway.coupang.com"

# =========================
# DAILY LIFE TOPICS
# =========================

ITEMS = [
    {
        "keyword": "핸드폰 거치대",
        "pain": "영상 보다 손목 아픈 사람",
        "scene": "warm cozy bedroom at night, smartphone holder beside bed, soft lamp lighting, korean lifestyle, cinematic mood"
    },

    {
        "keyword": "수납 정리함",
        "pain": "방 정리가 자꾸 귀찮은 사람",
        "scene": "minimal clean korean room, organized storage box, cozy lifestyle, warm natural lighting"
    },

    {
        "keyword": "LED 무드등",
        "pain": "방 분위기를 바꾸고 싶은 사람",
        "scene": "dark cozy room with warm LED mood lamp, emotional korean interior, cinematic atmosphere"
    },

    {
        "keyword": "미니 청소기",
        "pain": "책상 먼지 신경 쓰이는 사람",
        "scene": "clean desk setup, tiny vacuum cleaner, cozy korean workspace, warm tone"
    },

    {
        "keyword": "차량용 꿀템",
        "pain": "차 안이 자꾸 지저분해지는 사람",
        "scene": "clean modern car interior, korean lifestyle item, cinematic sunlight"
    },
]

# =========================
# COUPANG AUTH
# =========================

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

# =========================
# COUPANG DEEPLINK
# =========================

def make_coupang_deeplink(keyword):

    coupang_url = (
        "https://www.coupang.com/np/search?q="
        + urllib.parse.quote(keyword)
    )

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

        res = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )

        data = res.json()

        if "data" in data and len(data["data"]) > 0:

            return data["data"][0].get(
                "shortenUrl",
                coupang_url
            )

    except Exception:
        pass

    return coupang_url

# =========================
# THREADS TEXT
# =========================

def make_thread_text(keyword, pain):

    prompt = f"""
너는 한국 Threads에서 활동하는
감성 일상형 크리에이터다.

절대 광고처럼 쓰지 마라.

생활 속 작은 불편을 공감시키고,
사람들이 "나도 그런데…" 라고 느끼게 만들어라.

주제:
{keyword}

공감 대상:
{pain}

규칙:
- 실제 사람이 쓴 듯한 자연스러운 말투
- 광고 느낌 금지
- 쇼핑몰 느낌 금지
- 3~5문장
- 저장하고 싶은 느낌
- 댓글 달고 싶게
- 이모지 최대 1개
- "사세요"
- "구매"
- "최저가"
- "인생템"
- "대박"
전부 금지

좋은 느낌 예시:

"요즘 이런 작은 불편이 은근 쌓이더라구요.
별거 아닌데 반복되니까 꽤 피곤함…
생활 동선 조금 편해지는 게 생각보다 크네요.
나만 이런 거 느끼는 거 아니죠?"

이 톤으로 작성해라.
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=220
        )

        return str(
            response.choices[0].message.content
        ).strip()

    except Exception:

        return (
            f"{pain}이라면 이런 작은 불편이 은근 반복되죠. "
            "별거 아닌데 매일 겪다 보면 생각보다 피곤함… "
            "생활 동선 조금 편해지는 게 꽤 크더라구요. "
            "비슷한 거 느끼는 분 있나요?"
        )

# =========================
# AI IMAGE
# =========================

def make_ai_image(scene):

    try:

        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"""
instagram threads lifestyle photography,
korean emotional lifestyle,
minimal aesthetic,
warm cinematic lighting,
soft shadows,
natural realistic photo,
NO text,
NO watermark,
high quality,
{scene}
""",
            size="1024x1024"
        )

        image_base64 = result.data[0].b64_json

        import base64

        image_bytes = base64.b64decode(image_base64)

        return Image.open(io.BytesIO(image_bytes))

    except Exception:
        return None

# =========================
# FONT
# =========================

def get_font(size):

    paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf"
    ]

    for p in paths:

        if os.path.exists(p):

            return ImageFont.truetype(p, size)

    return ImageFont.load_default()

# =========================
# CARD NEWS
# =========================

def make_card_news(keyword, thread_text):

    width = 1080
    height = 1350

    img = Image.new(
        "RGB",
        (width, height),
        (18, 19, 27)
    )

    draw = ImageDraw.Draw(img)

    title_font = get_font(70)
    body_font = get_font(44)
    small_font = get_font(30)

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

    wrapped = textwrap.fill(
        thread_text,
        width=17
    )

    draw.text(
        (95, 360),
        wrapped,
        fill=(235, 235, 240),
        font=body_font,
        spacing=18
    )

    draw.text(
        (95, 1180),
        "저장해두면 좋은 생활 아이디어",
        fill=(150, 150, 160),
        font=small_font
    )

    buffer = io.BytesIO()

    img.save(buffer, format="PNG")

    buffer.seek(0)

    return img, buffer

# =========================
# UI
# =========================

st.set_page_config(
    page_title="Daily Life Threads Studio",
    page_icon="🔥",
    layout="centered"
)

st.title("🔥 Daily Life Threads Studio")

st.write(
    "감성 라이프스타일 이미지 + 공감형 Threads + 저장용 카드뉴스 생성"
)

count = st.slider(
    "자동 생성 개수",
    1,
    10,
    3
)

# =========================
# BUTTON
# =========================

if st.button("🚀 오늘의 Threads 생성"):

    selected = random.sample(
        ITEMS,
        count
    )

    for item in selected:

        keyword = item["keyword"]
        pain = item["pain"]
        scene = item["scene"]

        thread_text = make_thread_text(
            keyword,
            pain
        )

        partner_url = make_coupang_deeplink(
            keyword
        )

        ai_image = make_ai_image(
            scene
        )

        card_img, card_buffer = make_card_news(
            keyword,
            thread_text
        )

        st.divider()

        st.subheader(f"🔥 {keyword}")

        # =====================
        # AI IMAGE
        # =====================

        if ai_image:

            st.image(
                ai_image,
                caption="감성 라이프스타일 이미지"
            )

        # =====================
        # THREADS TEXT
        # =====================

        st.text_area(
            "Threads 본문",
            thread_text,
            height=220
        )

        # =====================
        # CARD NEWS
        # =====================

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

        # =====================
        # COMMENT LINK
        # =====================

        st.text_area(
            "댓글용 쿠팡파트너스 링크",
            f"참고했던 제품은 여기예요👇\n{partner_url}",
            height=100
        )

st.caption(
    "Daily Life Threads Studio + Coupang Partners"
)
