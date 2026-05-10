import streamlit as st
import random
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# =========================
# API
# =========================

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# 페이지 설정
# =========================

st.set_page_config(
    page_title="Threads AI 자동화",
    page_icon="🔥",
    layout="centered"
)

st.title("🔥 Threads AI 수익 자동화")

st.write("광고티 없이 Threads 최적화 글 + 카드뉴스 생성")

# =========================
# 자동 키워드
# =========================

keywords = [
    "차량용 쓰레기통",
    "핸드폰 거치대",
    "자취 꿀템",
    "캠핑 랜턴",
    "무선 청소기",
    "차량 방향제",
    "욕실 꿀템",
    "미니 가습기",
    "USB 선풍기",
    "책상 정리함",
]

# =========================
# Threads 문체 생성
# =========================

def make_thread(keyword):

    prompt = f"""
다음 조건으로 Threads 글 작성.

주제:
{keyword}

조건:
- 광고 느낌 금지
- 친구 추천 느낌
- 실제 사용 후기 느낌
- 저장하고 싶은 느낌
- 공감 + 궁금증 유발
- 너무 길지 않게
- 100~180자
- 이모지 1~2개
- 자연스러운 한국인 말투

절대 하지 말 것:
- 인생템
- 무조건 사세요
- 링크 클릭
- 광고 문구
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# =========================
# 카드뉴스 생성
# =========================

def make_card(keyword, text):

    img = Image.new("RGB", (1080, 1350), color=(10, 10, 15))

    draw = ImageDraw.Draw(img)

    title = f"🔥 {keyword}"

    body = textwrap.fill(text, width=18)

    draw.text((60, 80), title, fill="white")

    draw.text((60, 260), body, fill="white")

    filename = f"{keyword}.png"

    img.save(filename)

    return filename

# =========================
# UI
# =========================

count = st.slider("자동 생성 개수", 1, 10, 3)

if st.button("🚀 오늘의 Threads 자동 생성"):

    for i in range(count):

        keyword = random.choice(keywords)

        thread_text = make_thread(keyword)

        # 쿠팡 검색 링크
        coupang_url = (
            "https://www.coupang.com/np/search?q="
            + keyword
        )

        # 카드뉴스 생성
        image_file = make_card(keyword, thread_text)

        st.divider()

        st.subheader(f"🔥 {keyword}")

        st.text_area(
            "Threads 본문",
            thread_text,
            height=160
        )

        st.text_area(
            "댓글용 쿠팡 링크",
            f"🔗 제품 정보\n{coupang_url}",
            height=90
        )

        st.image(image_file)

        with open(image_file, "rb") as file:
            st.download_button(
                label="📥 카드뉴스 다운로드",
                data=file,
                file_name=image_file,
                mime="image/png"
            )

st.divider()

st.caption("Threads AI 자동화 시스템")
