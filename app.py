import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
import requests
import urllib.parse
import io
import json
import re
from datetime import datetime

st.set_page_config(page_title="AI 최신 이슈 블로그 & 썸네일 생성기", layout="wide")
st.title("🚀 AI 최신 이슈 블로그 글 & 썸네일 생성기")
st.caption("최신 웹 정보를 확인한 뒤 블로그 본문·FAQ·본문 연동 썸네일을 생성합니다.")

with st.sidebar:
    st.header("🔑 설정")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    st.caption("API Key는 이 화면에서만 사용합니다.")

keyword = st.text_input("주제 키워드 입력", placeholder="예: 아시안게임 축구 금메달")

def extract_json(text):
    text = text.strip()
    text = re.sub(r"^\x60\x60\x60(?:json)?", "", text, flags=re.I).strip()
    text = re.sub(r"\x60\x60\x60$", "", text).strip()
    return json.loads(text)

def make_thumbnail(keyword, title, image_prompt):
    # AI는 글자 없는 배경만 생성하고, 한글 제목은 Python으로 정확하게 합성
    prompt = (
        f"{image_prompt}. Korean news blog thumbnail background, photorealistic, "
        "editorial sports/news photography, no letters, no words, no typography, "
        "no Chinese characters, no Japanese characters, no watermark, 16:9"
    )
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + "?width=1200&height=675&nologo=true&enhance=true"
    )
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle((0, 420, 1200, 675), fill=(0, 0, 0, 175))

    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_path = next((p for p in font_paths if __import__("os").path.exists(p)), None)
    font = ImageFont.truetype(font_path, 54) if font_path else ImageFont.load_default()

    clean_title = re.sub(r"[#*_]", "", title).strip()
    # 길면 두 줄로 나누기
    words = clean_title.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textbbox((0, 0), test, font=font)[2] > 1080 and line:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    lines = lines[:2]

    y = 455
    for line in lines:
        draw.text((60, y), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
        y += 72

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()

if st.button("AI 콘텐츠 생성하기", type="primary"):
    if not gemini_api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해주세요.")
    elif not keyword.strip():
        st.warning("키워드를 입력해주세요.")
    else:
        status = st.status("최신 정보를 확인하고 있습니다...", expanded=True)
        try:
            client = genai.Client(
                api_key=gemini_api_key,
                http_options=types.HttpOptions(timeout=45000),
            )

            today = datetime.now().strftime("%Y-%m-%d")
            status.write("1/3 최신 웹 정보 검색 중... (Gemini 3.8 Flash 1회만 사용)")

            research_prompt = f"""
오늘 날짜는 {today}입니다.
사용자 키워드는 '{keyword}'입니다.

반드시 Google Search를 사용해서 이 키워드의 '현재/최신 사건'을 먼저 확인하세요.
과거의 유명한 사건을 최신 사건인 것처럼 대신 쓰면 안 됩니다.
오늘 또는 최근에 실제 사건이 있다면 날짜, 경기/사건 결과, 인물, 점수, 장소 등 핵심 사실을 교차 확인하세요.
최신 사건을 확인할 수 없다면 억지로 만들지 말고 그 사실을 명시하세요.

검색 결과를 바탕으로 아래 JSON 하나만 반환하세요.
{{
  "latest_summary": "최신 사실 요약",
  "facts": ["확인된 사실 1", "확인된 사실 2", "확인된 사실 3"],
  "source_notes": ["출처/매체와 확인 포인트"],
  "event_date": "YYYY-MM-DD 또는 확인 불가"
}}
"""
            research = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=research_prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.1,
                    max_output_tokens=1200,
                ),
            )
            research_text = research.text or ""
            try:
                research_data = extract_json(research_text)
            except Exception:
                research_data = {
                    "latest_summary": research_text,
                    "facts": [],
                    "source_notes": [],
                    "event_date": "확인 불가",
                }

            status.write("2/3 확인된 최신 사실로 블로그 작성 중... (Flash Lite 사용)")
            writing_prompt = f"""
오늘 날짜: {today}
사용자 키워드: {keyword}

아래는 방금 웹 검색으로 확인한 최신 정보입니다.
{json.dumps(research_data, ensure_ascii=False)}

이 자료만을 핵심 사실의 근거로 사용해 최신 이슈 블로그 글을 작성하세요.
예전 아시안게임이나 과거 사건을 본문 중심으로 길게 설명하지 마세요.
사용자가 최신 사건을 검색했다면 첫 문단부터 최신 결과를 바로 알려주세요.
확인되지 않은 선수명, 점수, 날짜, 기록은 만들지 마세요.

반드시 JSON 하나만 반환하세요.
{{
  "title": "검색 클릭을 유도하되 과장하지 않은 한국어 제목",
  "blog_markdown": "최신 사건 중심의 한국어 블로그 본문. 제목 다음에 요약, 핵심 결과, 경기/사건 흐름, 의미, 알아둘 점 순서. 1200~1800자 정도.",
  "faq": [
    {{"q":"질문1","a":"답변1"}},
    {{"q":"질문2","a":"답변2"}},
    {{"q":"질문3","a":"답변3"}}
  ],
  "thumbnail_prompt": "본문의 실제 사건을 시각화하는 구체적인 영어 이미지 프롬프트. 축구라면 football stadium, Korean national team celebration, gold medal 등 실제 주제 요소를 반드시 포함. 특정 실존 인물 얼굴 복제는 요구하지 말 것."
}}
"""
            # 3.8은 검색에만 1회 사용하고, 글쓰기는 한도가 넉넉한 Flash Lite로 분리
            writing_models = ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite"]
            written = None
            writing_error = None
            for writing_model in writing_models:
                try:
                    written = client.models.generate_content(
                        model=writing_model,
                        contents=writing_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.35,
                            max_output_tokens=2400,
                            response_mime_type="application/json",
                        ),
                    )
                    status.write(f"글 작성 모델: {writing_model}")
                    break
                except Exception as e:
                    writing_error = e
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        continue
                    raise
            if written is None:
                raise RuntimeError(f"글쓰기 모델 사용량 제한에 걸렸습니다: {writing_error}")
            data = extract_json(written.text or "{}")

            title = data.get("title", keyword)
            blog = data.get("blog_markdown", "")
            faq = data.get("faq", [])
            image_prompt = data.get(
                "thumbnail_prompt",
                f"football stadium, South Korean team celebrating a gold medal, {keyword}",
            )

            schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item.get("q", ""),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": item.get("a", ""),
                        },
                    }
                    for item in faq
                ],
            }

            status.write("3/3 본문 내용에 맞는 썸네일 생성 중...")
            thumb = None
            thumb_error = None
            try:
                thumb = make_thumbnail(keyword, title, image_prompt)
            except Exception as e:
                thumb_error = str(e)

            status.update(label="콘텐츠 생성 완료", state="complete", expanded=False)

            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("📝 생성된 최신 블로그 글")
                st.markdown(f"# {title}\n\n{blog}")
                st.subheader("⚙️ FAQ 스키마 마크업")
                st.code(
                    '<script type="application/ld+json">\n'
                    + json.dumps(schema, ensure_ascii=False, indent=2)
                    + '\n</script>',
                    language="html",
                )
                with st.expander("이번 글에 사용한 최신 정보 확인 내용"):
                    st.write(research_data)

            with col2:
                st.subheader("🖼️ 본문 연동 썸네일")
                if thumb:
                    st.image(thumb, use_container_width=True)
                    st.download_button(
                        "썸네일 JPG 다운로드",
                        data=thumb,
                        file_name="thumbnail.jpg",
                        mime="image/jpeg",
                    )
                else:
                    st.warning("본문은 생성됐지만 썸네일 생성에 실패했습니다.")
                    st.code(thumb_error or "알 수 없는 오류")

        except Exception as e:
            try:
                status.update(label="생성 실패", state="error", expanded=True)
            except Exception:
                pass
            st.error("콘텐츠 생성 중 오류가 발생했습니다.")
            st.code(str(e))
