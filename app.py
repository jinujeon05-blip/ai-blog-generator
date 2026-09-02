import os
import time
import requests
import html
from io import BytesIO
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import streamlit as st

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 0. 페이지 설정은 다른 st 명령보다 먼저 호출되어야 합니다.
st.set_page_config(page_title="Jinwoo | AI Blog Studio", page_icon="🤖", layout="centered")

# 1. 스트림릿 비밀 보관함에서 키를 가져옵니다.
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY_2"])


# 🎨 배경·버튼·입력창 커스텀 스타일 + Jinwoo 로고
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(160deg, #F4F1FE 0%, #EAF6FB 45%, #FDF6F0 100%);
    }
    .jw-logo-wrap {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 4px 0 28px 0;
    }
    .jw-logo-mark {
        width: 52px;
        height: 52px;
        border-radius: 16px;
        background: linear-gradient(135deg, #6C5CE7 0%, #00B4D8 100%);
        box-shadow: 0 6px 16px rgba(108, 92, 231, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .jw-logo-mark span {
        font-family: 'Georgia', serif;
        font-weight: 700;
        font-size: 26px;
        color: #ffffff;
    }
    .jw-logo-text {
        display: flex;
        flex-direction: column;
        line-height: 1.15;
    }
    .jw-logo-text .jw-name {
        font-size: 22px;
        font-weight: 800;
        background: linear-gradient(90deg, #6C5CE7, #00B4D8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.3px;
    }
    .jw-logo-text .jw-sub {
        font-size: 12px;
        font-weight: 600;
        color: #8A8FA3;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .stTextArea textarea, .stTextInput input {
        border-radius: 12px !important;
        border: 1px solid #E3E1F7 !important;
        box-shadow: 0 2px 6px rgba(108, 92, 231, 0.06);
    }
    div[data-testid="stFileUploaderDropzone"] {
        border-radius: 14px !important;
        border: 1.5px dashed #B9AEF0 !important;
        background: #FBFAFF !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #6C5CE7 0%, #00B4D8 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 0.6em 1.6em;
        font-weight: 700;
        letter-spacing: 0.2px;
        box-shadow: 0 6px 16px rgba(108, 92, 231, 0.3);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(108, 92, 231, 0.4);
        color: #ffffff;
    }
    .stDownloadButton > button {
        background: linear-gradient(90deg, #00B4D8 0%, #6C5CE7 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 6px 16px rgba(0, 180, 216, 0.3);
    }
    </style>

    <div class="jw-logo-wrap">
        <div class="jw-logo-mark"><span>J</span></div>
        <div class="jw-logo-text">
            <span class="jw-name">Jinwoo</span>
            <span class="jw-sub">AI Blog Studio</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# 모델 과부하(503)·요청 과다(429) 시 잠시 대기 후 재시도
def generate_with_retry(max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            msg = str(e)
            is_retryable = "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
            if is_retryable and attempt < max_retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise

# 🌍 UI 다국어 사전 정의
ui_texts = {
    "한국어": {
        "title": "🤖 AI 블로그 자동화 생성기",
        "lang_select": "🌐 화면 언어 선택",
        "input_mode": "📥 소스 입력 방식을 선택하세요",
        "mode_url": "웹사이트 링크 입력",
        "mode_text": "직접 본문 텍스트 입력",
        "mode_video": "영상 파일 업로드",
        "url_label": "분석할 웹사이트 링크 입력",
        "text_label": "블로그 원고로 변환할 본문 내용을 직접 붙여넣으세요",
        "video_label": "블로그로 변환할 영상 파일을 업로드하세요 (MP4, MOV 등)",
        "text_placeholder": "여기에 상품 설명, 뉴스 기사, 또는 참고할 텍스트를 복사해서 붙여넣으세요...",
        "prompt_label": "AI 마케팅 지시사항",
        "default_prompt": "10년 차 블로그 마케터처럼 작성해줘",
        "button": "블로그 원고 생성하기",
        "spinner_url": "🔄 정보를 수집하고 있습니다...",
        "spinner_video": "🔄 영상을 업로드하고 AI가 분석 중입니다...",
        "spinner_ai": "✨ 제미나이가 마케팅 원고를 작성하고 있습니다...",
        "success": "✨ 블로그 원고가 완성되었습니다!",
        "copy_header": "📋 원고 텍스트 직접 복사",
        "copy_placeholder": "아래 상자의 내용을 복사해서 사용하세요.",
        "err_url": "링크를 입력해주세요!",
        "err_text": "본문 내용을 입력해주세요!",
        "err_video": "영상 파일을 업로드해주세요!",
        "trans_header": "🌐 생성된 원고 추가 번역",
        "trans_label": "번역할 언어를 선택하세요",
        "trans_btn": "원고 번역하기",
        "spinner_trans": "🔄 원고를 번역하고 있습니다...",
        "trans_success": "✨ 번역이 완료되었습니다!",
        "pdf_btn": "📥 PDF로 다운로드",
    },
    "영어 (English)": {
        "title": "🤖 AI Blog Automation Generator",
        "lang_select": "🌐 Select UI Language",
        "input_mode": "📥 Select Source Input Method",
        "mode_url": "Website Link Input",
        "mode_text": "Direct Text Input",
        "mode_video": "Video File Upload",
        "url_label": "Enter Website Link to Analyze",
        "text_label": "Paste the body text to convert into a blog post",
        "video_label": "Upload a video file to convert into a blog post (MP4, MOV, etc.)",
        "text_placeholder": "Paste product descriptions, news articles, or reference text here...",
        "prompt_label": "AI Marketing Instructions",
        "default_prompt": "Write like a 10-year veteran blog marketer with high engagement.",
        "button": "Generate Blog Post",
        "spinner_url": "🔄 Gathering information...",
        "spinner_video": "🔄 Uploading video and analyzing with AI...",
        "spinner_ai": "✨ Gemini is crafting your marketing copy...",
        "success": "✨ Blog post successfully generated!",
        "copy_header": "📋 Direct Copy Text Area",
        "copy_placeholder": "Copy the content from the box below.",
        "err_url": "Please enter a link!",
        "err_text": "Please enter body content!",
        "err_video": "Please upload a video file!",
        "trans_header": "🌐 Additional Post Translation",
        "trans_label": "Select language to translate",
        "trans_btn": "Translate Post",
        "spinner_trans": "🔄 Translating the post...",
        "trans_success": "✨ Translation completed!",
        "pdf_btn": "📥 Download as PDF",
    },
    "베트남어 (Tiếng Việt)": {
        "title": "🤖 Trình Tạo Blog Tự Động AI",
        "lang_select": "🌐 Chọn Ngôn Ngữ Giao Diện",
        "input_mode": "📥 Chọn Phương Thức Nhập Nguồn",
        "mode_url": "Nhập Liên Kết Trang Web",
        "mode_text": "Nhập Văn Bản Trực Tiếp",
        "mode_video": "Tải Lên Tệp Video",
        "url_label": "Nhập liên kết trang web cần phân tích",
        "text_label": "Dán nội dung văn bản để chuyển đổi thành bài đăng blog",
        "video_label": "Tải lên tệp video để chuyển đổi thành bài viết blog",
        "text_placeholder": "Dán mô tả sản phẩm, bài báo hoặc văn bản tham khảo vào đây...",
        "prompt_label": "Hướng Dẫn Tiếp Thị AI",
        "default_prompt": "Viết như một nhà tiếp thị blog 10 năm kinh nghiệm.",
        "button": "Tạo Bài Viết Blog",
        "spinner_url": "🔄 Đang thu thập thông tin...",
        "spinner_video": "🔄 Đang tải lên video và phân tích bằng AI...",
        "spinner_ai": "✨ Gemini đang soạn thảo nội dung tiếp thị cho bạn...",
        "success": "✨ Bài viết blog đã được hoàn thành!",
        "copy_header": "📋 Khu Vực Sao Chép Văn Bản Trực Tiếp",
        "copy_placeholder": "Sao chép nội dung từ ô bên dưới để sử dụng.",
        "err_url": "Vui lòng nhập liên kết!",
        "err_text": "Vui lòng nhập nội dung văn bản!",
        "err_video": "Vui lòng tải lên tệp video!",
        "trans_header": "🌐 Dịch Bổ Sung Bài Viết",
        "trans_label": "Chọn ngôn ngữ để dịch",
        "trans_btn": "Dịch Bài Viết",
        "spinner_trans": "🔄 Đang dịch bài viết...",
        "trans_success": "✨ Đã dịch xong!",
        "pdf_btn": "📥 Tải xuống dưới dạng PDF",
    },
    "일본어 (日本語)": {
        "title": "🤖 AI ブログ自動化ジェネレーター",
        "lang_select": "🌐 UI言語の選択",
        "input_mode": "📥 ソース入力方法を選択してください",
        "mode_url": "ウェブサイトリンク入力",
        "mode_text": "直接本文テキスト入力",
        "mode_video": "動画ファイルアップロード",
        "url_label": "分析するウェブサイトのリンクを入力",
        "text_label": "ブログ原稿に変換する本文の内容を直接貼り付けてください",
        "video_label": "ブログに変換する動画ファイルをアップロードしてください",
        "text_placeholder": "ここに商品説明、ニュース記事、または参考テキストを貼り付けてください...",
        "prompt_label": "AIマーケティング指示事項",
        "default_prompt": "10年目のプロブログマーケターのように書いてください。",
        "button": "ブログ原稿を生成する",
        "spinner_url": "🔄 情報を収集中です...",
        "spinner_video": "🔄 動画をアップロードし、AIが分析中です...",
        "spinner_ai": "✨ Geminiがマーケティング原稿を作成しています...",
        "success": "✨ ブログ原稿が完成しました！",
        "copy_header": "📋 原稿テキスト直接コピー",
        "copy_placeholder": "下のボックスの内容をコピーしてご使用ください。",
        "err_url": "リンクを入力してください！",
        "err_text": "本文の内容を入力してください！",
        "err_video": "動画ファイルをアップロードしてください！",
        "trans_header": "🌐 生成された原稿の追加翻訳",
        "trans_label": "翻訳する言語を選択してください",
        "trans_btn": "原稿を翻訳する",
        "spinner_trans": "🔄 原稿を翻訳しています...",
        "trans_success": "✨ 翻訳が完了しました！",
        "pdf_btn": "📥 PDFとしてダウンロード",
    },
}

# 상단 UI 언어 선택
selected_lang = st.selectbox(
    "🌐 Language / 언어 / Ngôn ngữ / 言語",
    ["한국어", "영어 (English)", "베트남어 (Tiếng Việt)", "일본어 (日本語)"],
)
t = ui_texts[selected_lang]

st.title(t["title"])

# 입력 방식 선택 옵션
input_mode = st.radio(
    t["input_mode"], [t["mode_url"], t["mode_text"], t["mode_video"]]
)

scraped_text = ""
video_file_obj = None

if input_mode == t["mode_url"]:
    url = st.text_input(t["url_label"], "https://news.naver.com")
elif input_mode == t["mode_text"]:
    manual_text = st.text_area(
        t["text_label"], height=150, placeholder=t["text_placeholder"]
    )
else:
    uploaded_video = st.file_uploader(
        t["video_label"], type=["mp4", "mov", "avi", "mkv", "webm"]
    )

prompt_cmd = st.text_area(t["prompt_label"], t["default_prompt"])

# 세션 상태 초기화
if "generated_post" not in st.session_state:
    st.session_state.generated_post = ""

if st.button(t["button"]):
    if input_mode == t["mode_url"]:
        if not url:
            st.warning(t["err_url"])
            st.stop()
        else:
            with st.spinner(t["spinner_url"]):
                try:
                    response = requests.get(
                        url, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    text_content = ""
                    for p in soup.find_all("p"):
                        text_content += p.get_text() + " "
                    scraped_text = text_content[:2000]
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.stop()

    elif input_mode == t["mode_text"]:
        if not manual_text.strip():
            st.warning(t["err_text"])
            st.stop()
        else:
            scraped_text = manual_text[:2000]

    else:
        if not uploaded_video:
            st.warning(t["err_video"])
            st.stop()
        else:
            with st.spinner(t["spinner_video"]):
                try:
                    video_file_obj = client.files.upload(
                        file=uploaded_video,
                        config={"mime_type": uploaded_video.type},
                    )
                    while video_file_obj.state.name == "PROCESSING":
                        time.sleep(2)
                        video_file_obj = client.files.get(name=video_file_obj.name)
                    if video_file_obj.state.name == "FAILED":
                        raise ValueError("영상 파일 처리에 실패했습니다.")
                except Exception as e:
                    st.error(f"영상 업로드 중 오류가 발생했습니다: {e}")
                    st.stop()

    # AI 모델 호출
    with st.spinner(t["spinner_ai"]):
        try:
            if video_file_obj:
                contents = [
                    video_file_obj,
                    "다음 영상을 바탕으로 매력적인 블로그 홍보 글을 작성해줘.",
                ]
            else:
                contents = f"다음 정보를 바탕으로 블로그 홍보 글을 작성해줘:\n\n{scraped_text}"

            response_ai = generate_with_retry(
                model="gemini-3.5-flash-lite",
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=prompt_cmd),
            )
            st.session_state.generated_post = response_ai.text
        except Exception as e:
            st.error(f"AI 생성 중 오류가 발생했습니다: {e}")


# 💡 확실한 한글 깨짐 방지: 구글 폰트 자동 다운로드 및 적용 함수
def get_korean_font():
    font_path = "NanumGothic.ttf"
    # 서버에 폰트 파일이 없으면 구글 폰트에서 직접 다운로드합니다.
    if not os.path.exists(font_path):
        font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        try:
            r = requests.get(font_url)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            st.error(f"폰트 다운로드 실패: {e}")
            return "Helvetica" # 최후의 수단
    
    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
    return "NanumGothic"


# PDF 생성 함수
def create_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    story = []

    # 폰트를 준비하고 스타일을 지정합니다.
    font_name = get_korean_font()
    styles = getSampleStyleSheet()
    
    kor_style = ParagraphStyle(
        "KoreanStyle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=16,
    )

    # 마크다운 특수문자 및 줄바꿈 처리
    safe_text = html.escape(text).replace("\n", "<br/>")
    paragraph = Paragraph(safe_text, kor_style)
    story.append(paragraph)

    doc.build(story)
    buffer.seek(0)
    return buffer


# 이미 생성된 원고가 있는 경우 화면에 출력 및 다운로드/번역 기능 제공
if st.session_state.generated_post:
    st.success(t["success"])
    st.markdown("---")
    st.markdown(st.session_state.generated_post)

    # 📥 PDF 다운로드 버튼
    st.markdown("---")
    pdf_data = create_pdf(st.session_state.generated_post)
    st.download_button(
        label=t["pdf_btn"],
        data=pdf_data,
        file_name="blog_post.pdf",
        mime="application/pdf",
    )

    # 🌐 번역 섹션
    st.markdown("---")
    st.subheader(t["trans_header"])
    target_lang = st.selectbox(
        t["trans_label"],
        [
            "한국어 (Korean)",
            "영어 (English)",
            "베트남어 (Tiếng Việt)",
            "일본어 (Japanese)",
        ],
    )

    if st.button(t["trans_btn"]):
        with st.spinner(t["spinner_trans"]):
            try:
                trans_prompt = (
                    f"다음 블로그 원고를 자연스러운 {target_lang}로 번역해줘."
                    f" 마케팅 톤앤매너를 유지해:\n\n{st.session_state.generated_post}"
                )
                trans_response = generate_with_retry(
                    model="gemini-3.5-flash-lite",
                    contents=trans_prompt,
                )
                st.session_state.generated_post = trans_response.text
                st.success(t["trans_success"])
                st.rerun()
            except Exception as e:
                st.error(f"번역 중 오류가 발생했습니다: {e}")

    # 📋 직접 복사 영역
    st.markdown("---")
    st.subheader(t["copy_header"])
    st.text_area(
        t["copy_placeholder"], st.session_state.generated_post, height=250
    )
