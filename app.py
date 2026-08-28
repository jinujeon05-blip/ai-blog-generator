import google.generativeai as genai
from bs4 import BeautifulSoup
import requests
import streamlit as st

# 1. 스트림릿 비밀 보관함에서 키를 가져옵니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 🌍 UI 다국어 사전 정의
ui_texts = {
    "한국어": {
        "title": "🤖 AI 블로그 자동화 생성기",
        "lang_select": "🌐 화면 언어 및 결과물 언어 선택",
        "input_mode": "📥 소스 입력 방식을 선택하세요",
        "mode_url": "웹사이트 링크 입력",
        "mode_text": "직접 본문 텍스트 입력",
        "url_label": "분석할 웹사이트 링크 입력",
        "text_label": "블로그 원고로 변환할 본문 내용을 직접 붙여넣으세요",
        "text_placeholder": (
            "여기에 상품 설명, 뉴스 기사, 또는 참고할 텍스트를 복사해서"
            " 붙여넣으세요..."
        ),
        "prompt_label": "AI 마케팅 지시사항",
        "default_prompt": "10년 차 블로그 마케터처럼 작성해줘",
        "button": "블로그 원고 생성하기",
        "spinner_url": "🔄 정보를 수집하고 있습니다...",
        "spinner_ai": "✨ 제미나이가 마케팅 원고를 작성하고 있습니다...",
        "success": "✨ 블로그 원고가 완성되었습니다!",
        "copy_header": "📋 원고 텍스트 직접 복사",
        "copy_placeholder": "아래 상자의 내용을 복사해서 사용하세요.",
        "err_url": "링크를 입력해주세요!",
        "err_text": "본문 내용을 입력해주세요!",
    },
    "영어 (English)": {
        "title": "🤖 AI Blog Automation Generator",
        "lang_select": "🌐 Select UI Language & Output Language",
        "input_mode": "📥 Select Source Input Method",
        "mode_url": "Website Link Input",
        "mode_text": "Direct Text Input",
        "url_label": "Enter Website Link to Analyze",
        "text_label": "Paste the body text to convert into a blog post",
        "text_placeholder": (
            "Paste product descriptions, news articles, or reference text"
            " here..."
        ),
        "prompt_label": "AI Marketing Instructions",
        "default_prompt": (
            "Write like a 10-year veteran blog marketer with high engagement."
        ),
        "button": "Generate Blog Post",
        "spinner_url": "🔄 Gathering information...",
        "spinner_ai": "✨ Gemini is crafting your marketing copy...",
        "success": "✨ Blog post successfully generated!",
        "copy_header": "📋 Direct Copy Text Area",
        "copy_placeholder": "Copy the content from the box below.",
        "err_url": "Please enter a link!",
        "err_text": "Please enter body content!",
    },
    "베트남어 (Tiếng Việt)": {
        "title": "🤖 Trình Tạo Blog Tự Động AI",
        "lang_select": "🌐 Chọn Ngôn Ngữ Giao Diện & Đầu Ra",
        "input_mode": "📥 Chọn Phương Thức Nhập Nguồn",
        "mode_url": "Nhập Liên Kết Trang Web",
        "mode_text": "Nhập Văn Bản Trực Tiếp",
        "url_label": "Nhập liên kết trang web cần phân tích",
        "text_label": "Dán nội dung văn bản để chuyển đổi thành bài đăng blog",
        "text_placeholder": (
            "Dán mô tả sản phẩm, bài báo hoặc văn bản tham khảo vào đây..."
        ),
        "prompt_label": "Hướng Dẫn Tiếp Thị AI",
        "default_prompt": (
            "Viết như một nhà tiếp thị blog 10 năm kinh nghiệm."
        ),
        "button": "Tạo Bài Viết Blog",
        "spinner_url": "🔄 Đang thu thập thông tin...",
        "spinner_ai": "✨ Gemini đang soạn thảo nội dung tiếp thị cho bạn...",
        "success": "✨ Bài viết blog đã được hoàn thành!",
        "copy_header": "📋 Khu Vực Sao Chép Văn Bản Trực Tiếp",
        "copy_placeholder": "Sao chép nội dung từ ô bên dưới để sử dụng.",
        "err_url": "Vui lòng nhập liên kết!",
        "err_text": "Vui lòng nhập nội dung văn bản!",
    },
    "일본어 (日本語)": {
        "title": "🤖 AI ブログ自動化ジェネレーター",
        "lang_select": "🌐 UI言語および出力言語の選択",
        "input_mode": "📥 ソース入力方法を選択してください",
        "mode_url": "ウェブサイトリンク入力",
        "mode_text": "直接本文テキスト入力",
        "url_label": "分析するウェブサイトのリンクを入力",
        "text_label": "ブログ原稿に変換する本文の内容を直接貼り付けてください",
        "text_placeholder": (
            "ここに商品説明、ニュース記事、または参考テキストを貼り付けてください..."
        ),
        "prompt_label": "AIマーケティング指示事項",
        "default_prompt": "10年目のプロブログマーケターのように書いてください。",
        "button": "ブログ原稿を生成する",
        "spinner_url": "🔄 情報を収集中です...",
        "spinner_ai": "✨ Geminiがマーケティング原稿を作成しています...",
        "success": "✨ ブログ原稿が完成しました！",
        "copy_header": "📋 原稿テキスト直接コピー",
        "copy_placeholder": "下のボックスの内容をコピーしてご使用ください。",
        "err_url": "リンクを入力してください！",
        "err_text": "本文の内容を入力してください！",
    },
}

# 상단 또는 사이드바에서 언어 선택 (UI 전체에 반영)
selected_lang = st.selectbox(
    "🌐 Language / 언어 / Ngôn ngữ / 言語",
    ["한국어", "영어 (English)", "베트남어 (Tiếng Việt)", "일본어 (日本語)"],
)
t = ui_texts[selected_lang]

st.title(t["title"])

# 입력 방식 선택 옵션
input_mode = st.radio(
    t["input_mode"], [t["mode_url"], t["mode_text"]]
)

scraped_text = ""

if input_mode == t["mode_url"]:
  url = st.text_input(t["url_label"], "https://news.naver.com")
else:
  manual_text = st.text_area(
      t["text_label"], height=150, placeholder=t["text_placeholder"]
  )

prompt_cmd = st.text_area(t["prompt_label"], t["default_prompt"])

if st.button(t["button"]):
  if input_mode == t["mode_url"]:
    if not url:
      st.warning(t["err_url"])
      st.stop()
    else:
      with st.spinner(t["spinner_url"]):
        try:
          response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
          response.raise_for_status()
          soup = BeautifulSoup(response.text, "html.parser")

          text_content = ""
          for p in soup.find_all("p"):
            text_content += p.get_text() + " "

          scraped_text = text_content[:2000]
        except Exception as e:
          st.error(f"Error: {e}")
          st.stop()
  else:
    if not manual_text.strip():
      st.warning(t["err_text"])
      st.stop()
    else:
      scraped_text = manual_text[:2000]

  if scraped_text.strip():
    with st.spinner(t["spinner_ai"]):
      try:
        model = genai.GenerativeModel(
            model_name="gemini-3.7-flash", system_instruction=prompt_cmd
        )

        lang_instruction = ""
        if "베트남어" in selected_lang:
          lang_instruction = (
              " 최종 결과물은 반드시 자연스러운 베트남어로 작성해줘."
          )
        elif "영어" in selected_lang:
          lang_instruction = (
              " 최종 결과물은 반드시 자연스러운 영어(English)로 작성해줘."
          )
        elif "일본어" in selected_lang:
          lang_instruction = (
              " 최종 결과물은 반드시 자연스러운 일본어(日本語)로 작성해줘."
          )
        else:
          lang_instruction = " 최종 결과물은 한국어로 작성해줘."

        prompt = (
            f"다음 정보를 바탕으로 블로그 홍보 글을 써줘.\n{lang_instruction}\n\n"
            f"{scraped_text}"
        )
        response_ai = model.generate_content(prompt)

        st.success(t["success"])
        st.markdown("---")

        # 결과 화면 출력
        st.markdown(response_ai.text)

        # 📋 직접 복사할 수 있는 텍스트 영역
        st.markdown("---")
        st.subheader(t["copy_header"])
        st.text_area(t["copy_placeholder"], response_ai.text, height=250)

      except Exception as e:
        st.error(f"Error: {e}")
