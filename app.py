import google.generativeai as genai
from bs4 import BeautifulSoup
import requests
import streamlit as st

# 1. 깃허브에 안전하게 올리기 위해 스트림릿 비밀 보관함에서 키를 가져옵니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🤖 AI 블로그 자동화 생성기")

url = st.text_input("분석할 웹사이트 링크 입력", "https://news.naver.com")
prompt_cmd = st.text_area(
    "AI 마케팅 지시사항", "10년 차 블로그 마케터처럼 작성해줘"
)

# 번역 언어 선택 옵션 추가
language_option = st.selectbox(
    "🌍 결과물 번역 언어 선택",
    ["한국어", "베트남어 (Tiếng Việt)", "영어 (English)", "일본어 (日本語)"],
)

if st.button("블로그 원고 생성하기"):
  if not url:
    st.warning("링크를 입력해주세요!")
  else:
    with st.spinner(
        "🔄 정보를 수집하고 제미나이가 원고를 작성하고 있습니다..."
    ):
      try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        text_content = ""
        for p in soup.find_all("p"):
          text_content += p.get_text() + " "

        scraped_text = text_content[:2000]

        if not scraped_text.strip():
          st.error("❌ 페이지에서 텍스트를 읽어오지 못했습니다.")
        else:
          # 이미지에 있는 최신 모델명으로 적용 (원하시는 경우 gemini-3.5-flash-lite 등으로 변경 가능)
          model = genai.GenerativeModel(
              model_name="gemini-3.7-flash", system_instruction=prompt_cmd
          )

          # 선택된 언어에 따른 프롬프트 지시사항 추가
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
        st.error(f"오류가 발생했습니다: {e}")
