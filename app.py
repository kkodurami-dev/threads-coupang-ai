import streamlit as st
import random
import urllib.parse
from openai import OpenAI

# =========================
# API KEY
# =========================
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# 자동 키워드 리스트
# =========================
AUTO_KEYWORDS = [
    "차량용 꿀템",
    "캠핑 꿀템",
    "자취 꿀템",
    "책상 정리 꿀템",
    "LED 무드등",
    "미니 청소기",
    "무선 충전기",
    "차박 꿀템",
    "주방 신박템",
    "욕실 꿀템",
    "생활 편의템",
    "수납 정리함",
    "집들이 선물",
    "직장인 책상템",
    "겨울 난방템",
    "여름 냉방템",
    "핸드폰 거치대",
    "블루투스 스피커",
    "생활 아이디어 상품",
    "다이소 감성템"
]

# =========================
# 쿠팡 검색 URL 생성
# =========================
def make_coupang_search_url(keyword):
    encoded = urllib.parse.quote(keyword)
    return f"https://www.coupang.com/np/search?q={encoded}"

# =========================
# AI 스레드 문구 생성
# =========================
def make_thread_text(keyword, url):

    prompt = f'''
다음 키워드 기반으로
Threads 실제 후기 느낌의 자연스러운 글 작성.

조건:
- 광고 느낌 금지
- 친구에게 추천하는 말투
- 과장 금지
- 짧고 자연스럽게
- 실사용 후기 느낌
- 저장하고 싶은 정보 느낌
- 이모지 최대 1~2개만
- 링크 언급 금지
- 80~140자

키워드:
{keyword}
'''

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# =========================
# 페이지 UI
# =========================
st.set_page_config(
    page_title="AI 신박템 생성기",
    page_icon="🔥",
    layout="centered"
)

st.title("🔥 AI 신박템 생성기")

st.write("버튼만 누르면 AI가 자동으로 오늘의 신박템 스레드 글 생성")

count = st.slider(
    "자동 생성 개수",
    1,
    10,
    5
)

# =========================
# 생성 버튼
# =========================
if st.button("🚀 오늘의 신박템 자동 생성"):

    selected_keywords = random.sample(AUTO_KEYWORDS, count)

    for keyword in selected_keywords:

        url = make_coupang_search_url(keyword)

        try:
            text = make_thread_text(keyword, url)
        except:
            text = f"🔥 요즘 난리난 {keyword}\n\n👉 {url}"

        st.divider()

        st.subheader(f"🔥 {keyword}")

        st.text_area(
            "스레드 본문 (게시용)",
            text,
            height=170
        )

        st.text_area(
    "댓글용 링크",
    f"🔗 제품 정보\n{url}",
    height=100
)

st.divider()

st.caption("Threads + 쿠팡파트너스 자동화 시스템")
