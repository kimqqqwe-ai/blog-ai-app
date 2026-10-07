import streamlit as st
import google.generativeai as genai
import urllib.parse

# Page config
st.set_page_config(page_title="AI 블로그 포스팅 & 썸네일 생성기", layout="wide")

st.title("🚀 AI 자동 블로그 글 & 썸네일 생성기")
st.caption("키워드만 입력하면 블로그 본문, 검색 노출용 FAQ 스키마, 썸네일을 한 번에 만들어줍니다.")

# 사이드바 API 키 입력
with st.sidebar:
    st.header("🔑 설정")
    gemini_api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.markdown("[Google AI Studio에서 무료 API Key 받기](https://aistudio.google.com/)")

# 메인 입력창
keyword = st.text_input("주제 키워드 입력", placeholder="예: 김무열 참교육")

if st.button("AI 콘텐츠 생성하기", type="primary"):
    if not gemini_api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해주세요!")
    elif not keyword:
        st.warning("키워드를 입력해주세요!")
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                with st.spinner("AI가 블로그 글과 스키마 마크업을 작성하고 있습니다..."):
                    # 1. 블로그 본문 생성
                    prompt_text = f"키워드 '{keyword}'에 대한 블로그 포스팅을 작성해줘. 제목, 서론, 본문(소제목 포함), 결론으로 전문적이고 흥미롭게 써줘."
                    res_text = model.generate_content(prompt_text)
                    
                    # 2. FAQ 스키마 생성
                    prompt_schema = f"키워드 '{keyword}' 관련 FAQ JSON-LD 스키마 마크업(<script type='application/ld+json'>)을 완성된 형태로 작성해줘."
                    res_schema = model.generate_content(prompt_schema)
                
                st.subheader("📝 생성된 블로그 글")
                st.write(res_text.text)
                
                st.subheader("⚙️ FAQ 스키마 마크업 (HTML용)")
                st.code(res_schema.text, language="html")

            with col2:
                with st.spinner("AI가 썸네일 이미지를 생성하고 있습니다..."):
                    # 3. 무료 썸네일 URL 생성
                    prompt_img = f"dramatic blog thumbnail for {keyword}, poster style, high quality"
                    encoded_prompt = urllib.parse.quote(prompt_img)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                
                st.subheader("🖼️ 생성된 썸네일")
                st.image(img_url, use_column_width=True)
                st.markdown(f"[이미지 다운로드 링크]({img_url})")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
