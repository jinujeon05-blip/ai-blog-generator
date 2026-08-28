import google.generativeai as genai
from bs4 import BeautifulSoup
import requests
import streamlit as st

# 1. 스트림릿 비밀 보관함에서 키를 가져옵니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🤖 AI 블로그 자동화 생성기")

# 입력 방식 선택 옵션 (링크 크롤링 vs 직접 텍스트 입력)
input_mode = st.radio(
    "📥 소스 입력 방식을 선택하세요", ["웹사이트 링크 입력", "직접 본문 텍스트 입력"]
)

scraped_text = ""

if input_mode == "웹사이트 링크 입력":
  url = st.text_input("분석할 웹사이트 링크 입력", "https://news.naver.com")
else:
  manual_text = st.text_area(
      "블로그 원고로 변환할 본문 내용을 직접 붙여넣으세요",
      height=150,
      placeholder=(
          "여기에 상품 설명, 뉴스 기사, 또는 참고할 텍스트를 복사해서"
          " 붙여넣으세요..."
      ),
  )

prompt_cmd = st.text_area(
    "AI 마케팅 지시사항", "10년 차 블로그 마케터처럼 작성해줘"
)

# 번역 언어 선택 옵션 추가
language_option = st.selectbox(
    "🌍 결과물 번역 언어 선택",
    ["한국어", "베트남어 (Tiếng Việt)", "영어 (English)", "일본어 (日本語)"],
)

if st.button("블로그 원고 생성하기"):
  if input_mode == "웹사이트 링크 입력":
    if not url:
      st.warning("링크를 입력해주세요!")
      st.stop()
    else:
      with st.spinner("🔄 정보를 수집하고 있습니다..."):
        try:
          response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
          response.raise_for_status()
          soup = BeautifulSoup(response.text, "html.parser")

          text_content = ""
          for p in soup.find_all("p"):
            text_content += p.get_text() + " "

          scraped_text = text_content[:2000]
        except Exception as e:
          st.error(f"링크를 읽어오는 중 오류가 발생했습니다: {e}")
          st.stop()
  else:
    if not manual_text.strip():
      st.warning("본문 내용을 입력해주세요!")
      st.stop()
    else:
      scraped_text = manual_text[:2000]

  if scraped_text.strip():
    with st.spinner("✨ 제미나이가 마케팅 원고를 작성하고 있습니다..."):
      try:
        model = genai.GenerativeModel(
            model_name="gemini-3.7-flash", system_instruction=prompt_cmd
        )

        lang_instruction = ""
        if "베트남어" in language_option:
          lang_instruction = (
              " 최종 결과물은 반드시 자연스러운 베트남어로 작성해줘."
          )
        elif "영어" in language_option:
          lang_instruction = " 최종 결과물은 반드시 자연스러운 영어로 작성해줘."
        elif "일본어" in language_option:
          lang_instruction = " 최종 결과물은 반드시 자연스러운 일본어로 작성해줘."
        else:
          lang_instruction = " 최종 결과물은 한국어로 작성해줘."

        prompt = (
            f"다음 정보를 바탕으로 블로그 홍보 글을 써줘.\n{lang_instruction}\n\n"
            f"{scraped_text}"
        )
        response_ai = model.generate_content(prompt)

        st.success("✨ 블로그 원고가 완성되었습니다!")
        st.markdown("---")

        # 결과 화면 출력
        st.markdown(response_ai.text)

        # 📋 직접 복사할 수 있는 텍스트 영역
        st.markdown("---")
        st.subheader("📋 원고 텍스트 직접 복사")
        st.text_area(
            "아래 상자의 내용을 복사해서 사용하세요.",
            response_ai.text,
            height=250,
        )

      except Exception as e:
        st.error(f"AI 원고 생성 중 오류가 발생했습니다: {e}")
