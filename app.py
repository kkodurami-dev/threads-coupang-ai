import io
import hmac
import hashlib
import urllib.parse
from datetime import datetime

import requests
import pandas as pd
import streamlit as st

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from openai import OpenAI

# ----------------------------
# API
# ----------------------------

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

COUPANG_ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
COUPANG_SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

COUPANG_DOMAIN = "https://api-gateway.coupang.com"

# ----------------------------
# 쿠팡 인증
# ----------------------------

def make_coupang_auth(method, path):

    now = datetime.utcnow().strftime("%y%m%dT%H%M%SZ")

    message = now + method + path

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

# ----------------------------
# 상품 검색
# ----------------------------

def search_coupang(keyword, limit=10):

    encoded = urllib.parse.quote(keyword)

    path = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={encoded}&limit={limit}"

    url = COUPANG_DOMAIN + path

    headers = {
        "Authorization": make_coupang_auth("GET", path),
        "Content-Type": "application/json"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        data = response.json()

        products = data.get(
            "data",
            {}
        ).get(
            "productData",
            []
        )

        results = []

        for p in products:

            results.append({
                "title": p.get("productName", ""),
                "price": p.get("productPrice", ""),
                "url": p.get("productUrl", ""),
                "image_url": p.get("productImage", "")
            })

        return results

    except:

        return []

# ----------------------------
# 신박템 점수
# ----------------------------

def novelty_score(title):

    words = [
        "미니",
        "무선",
        "휴대용",
        "접이식",
        "차량용",
        "LED",
        "수납",
        "거치대",
        "캠핑",
        "충전",
        "멀티",
        "정리",
        "자동",
    ]

    score = 0

    title = str(title)

    for w in words:

        if w in title:
            score += 10

    if len(title) <= 40:
        score += 10

    return score

# ----------------------------
# AI 후킹 생성
# ----------------------------

def make_copy(product):

    title = product["title"]

    prompt = f"""
너는 한국 Threads에서 활동하는
신박한 꿀템 계정 운영자다.

상품:
{title}

조건:

1. 광고처럼 보이면 안 된다.
2. 첫 문장은 강한 후킹.
3. 저장하고 싶은 느낌.
4. 짧고 중독성 있게.
5. 마지막은:
'링크는 댓글에 남겨둘게요.'
로 끝내라.
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except:

        return f"""
이거 왜 이제 알았지…

{title}

은근 만족감 높은 스타일.

링크는 댓글에 남겨둘게요.
"""

# ----------------------------
# 이미지 다운로드
# ----------------------------

def download_image(url):

    try:

        response = requests.get(url)

        img = Image.open(
            io.BytesIO(response.content)
        ).convert("RGB")

        return img

    except:

        return None

# ----------------------------
# 폰트
# ----------------------------

def get_font(size):

    try:

        return ImageFont.truetype(
            "arial.ttf",
            size
        )

    except:

        return ImageFont.load_default()

# ----------------------------
# 카드뉴스 생성
# ----------------------------

def create_card(product):

    width = 1080
    height = 1350

    bg = Image.new(
        "RGB",
        (width, height),
        (20,20,20)
    )

    draw = ImageDraw.Draw(bg)

    title = str(product["title"])[:30]

    font_big = get_font(60)
    font_small = get_font(42)

    draw.text(
        (80,100),
        "🧲 삶의 질 꿀템",
        fill=(255,215,0),
        font=font_big
    )

    draw.text(
        (80,240),
        title,
        fill=(255,255,255),
        font=font_small
    )

    img = download_image(
        product["image_url"]
    )

    if img:

        img.thumbnail((700,700))

        x = (width - img.width)//2

        bg.paste(
            img,
            (x,450)
        )

    return bg

# ----------------------------
# 화면
# ----------------------------

st.set_page_config(
    page_title="AI 신박템 생성기",
    layout="centered"
)

st.title("🔥 AI 신박템 생성기")

default_keywords = """
차량용 꿀템
캠핑 꿀템
자취 꿀템
책상 정리 꿀템
LED 무드등
미니 청소기
"""

keywords = st.text_area(
    "키워드 입력",
    default_keywords,
    height=180
)

limit = st.slider(
    "키워드당 상품 수",
    3,
    20,
    10
)

if st.button("🚀 생성 시작"):

    all_products = []

    with st.spinner("상품 수집 중..."):

        for keyword in keywords.splitlines():

            keyword = keyword.strip()

            if keyword:

                all_products.extend(
                    search_coupang(
                        keyword,
                        limit
                    )
                )

    if not all_products:

        st.warning("상품 없음")

    else:

        df = pd.DataFrame(all_products)

        df["score"] = df["title"].apply(
            novelty_score
        )

        df = df.sort_values(
            "score",
            ascending=False
        )

        for i, row in enumerate(df.head(10).iterrows()):

            product = row[1].to_dict()

            text = make_copy(product)

            image = create_card(product)

            st.image(image)

            st.text_area(
                f"본문 {i+1}",
                text,
                height=220
            )

            st.code(product["url"])
