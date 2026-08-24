import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. 깃허브에 안전하게 올리기 위해 스트림릿 비밀 보관함에서 키를 가져옵니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🤖 AI 블로그 자동화 생성기")

url = st.text_input("분석할 웹사이트 링크 입력", "https://news.naver.com")
prompt_cmd = st.text_area("AI 마케팅 지시사항", "10년 차 블로그 마케터처럼 작성해줘")

if st.button("블로그 원고 생성하기"):
    if not url:
        st.warning("링크를 입력해주세요!")
    else:
        with st.spinner("🔄 정보를 수집하고 제미나이가 원고를 작성하고 있습니다..."):
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                text_content = ""
                for p in soup.find_all('p'):
                    text_content += p.get_text() + " "
                    
                scraped_text = text_content[:2000]
                
                if not scraped_text.strip():
                    st.error("❌ 페이지에서 텍스트를 읽어오지 못했습니다.")
                else:
                    model = genai.GenerativeModel(
                        model_name='gemini-3.6-flash',
                        system_instruction=prompt_cmd
                    )
                    
                    prompt = f"다음 정보를 바탕으로 블로그 홍보 글을 써줘:\n\n{scraped_text}"
                    response_ai = model.generate_content(prompt)
                    
                    st.success("✨ 블로그 원고가 완성되었습니다!")
                    st.markdown("---")
                    st.markdown(response_ai.text)
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
