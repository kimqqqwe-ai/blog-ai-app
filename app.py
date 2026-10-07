import streamlit as st
from google import genai
from google.genai import types
import urllib.parse

st.set_page_config(page_title="AI 블로그 포스팅 & 썸네일 생성기", layout="wide")

st.title("🚀 AI 자동 블로그 글 & 썸네일 생성기")
st.caption("키워드만 입력하면 블로그 본문, 검색 노출용 FAQ 스키마, 썸네일을 한 번에 만들어줍니다.")

with st.sidebar:
    st.header("🔑 설정")
    gemini_api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.markdown("[Google AI Studio에서 무료 API Key 받기](https://aistudio.google.com/)")

keyword = st.text_input("주제 키워드 입력", placeholder="예: 김무열 참교육")

if st.button("AI 콘텐츠 생성하기", type="primary"):
    if not gemini_api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해주세요!")
    elif not keyword:
        st.warning("키워드를 입력해주세요!")
    else:
        try:
            status = st.status("AI 콘텐츠 생성을 시작합니다...", expanded=True)
            status.write("1/3 Gemini 3.8 Flash 연결 및 블로그·FAQ 생성 중...")

            client = genai.Client(
                api_key=gemini_api_key,
                http_options=types.HttpOptions(timeout=60000),
            )

            prompt = f"""
키워드: {keyword}

아래 두 결과를 한 번에 작성해주세요.

[블로그 본문]
- 검색 사용자의 궁금증을 바로 해결하는 제목
- 자연스러운 서론
- 소제목이 있는 충분히 자세한 본문
- 핵심 요약과 결론
- 과장되거나 확인되지 않은 사실은 단정하지 말 것
- 한국어로 작성

[FAQ 스키마]
- 위 주제와 직접 관련된 FAQ 5개
- 완전한 <script type="application/ld+json">...</script> 형식
- Schema.org FAQPage 규격 사용

반드시 아래 구분자를 정확히 사용하세요.

===BLOG===
블로그 본문
===SCHEMA===
FAQ JSON-LD
"""

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            result = response.text or ""
            if "===BLOG===" not in result or "===SCHEMA===" not in result:
                raise ValueError("Gemini 응답 형식이 예상과 다릅니다. 다시 시도해주세요.")

            blog_part = result.split("===BLOG===", 1)[1].split("===SCHEMA===", 1)[0].strip()
            schema_part = result.split("===SCHEMA===", 1)[1].strip()

            status.write("2/3 블로그 본문과 FAQ 생성 완료")
            status.write("3/3 썸네일 주소 생성 완료")
            status.update(label="콘텐츠 생성 완료", state="complete", expanded=False)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📝 생성된 블로그 글")
                st.markdown(blog_part)

                st.subheader("⚙️ FAQ 스키마 마크업 (HTML용)")
                st.code(schema_part, language="html")

            with col2:
                prompt_img = f"dramatic professional blog thumbnail for {keyword}, poster style, high quality, no text"
                encoded_prompt = urllib.parse.quote(prompt_img)
                img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

                st.subheader("🖼️ 생성된 썸네일")
                st.image(img_url, use_container_width=True)
                st.markdown(f"[이미지 열기]({img_url})")

        except Exception as e:
            try:
                status.update(label="생성 실패", state="error", expanded=True)
            except Exception:
                pass
            st.error("콘텐츠 생성 중 오류가 발생했습니다.")
            st.code(str(e))
            st.info("오류 내용을 그대로 보내주시면 바로 다음 수정에 반영할 수 있습니다.")
