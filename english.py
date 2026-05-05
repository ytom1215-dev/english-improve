import streamlit as st
import google.generativeai as genai
import json
import os
import base64

# ============================================================
# 1. ページ設定とスタイル
# ============================================================
st.set_page_config(
    page_title="AgriEnglish i+1 (Gemini 3 Powered)",
    page_icon="🌱",
    layout="centered"
)

st.markdown("""
    <style>
    .main { background-color: #fcfdfc; }
    .stButton>button { border-radius: 20px; }
    .reading-box {
        font-size: 1.15rem;
        line-height: 1.8;
        padding: 1.8rem;
        background-color: #ffffff;
        border: 1px solid #e0eadd;
        border-left: 8px solid #2e7d32;
        border-radius: 12px;
        color: #2c3e50;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .vocab-card {
        background-color: #f1f8e9;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# 2. 定数・ファイル操作
# ============================================================
LESSONS_FILE = "lessons_v2.json"

def load_lessons():
    if os.path.exists(LESSONS_FILE):
        try:
            with open(LESSONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_lessons(lessons: dict):
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

def text_to_speech_js(text):
    b64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    js_code = f"""
        <button onclick="
            var msg = new SpeechSynthesisUtterance(atob('{b64_text}'));
            msg.lang = 'en-US';
            msg.rate = 0.85;
            window.speechSynthesis.speak(msg);
        " style="
            background-color: #2e7d32; border: none; color: white;
            padding: 8px 20px; border-radius: 20px; cursor: pointer;
            font-weight: bold; margin-bottom: 10px;
        ">🔊 Listen to Text</button>
    """
    return js_code

# ============================================================
# 3. セッション状態
# ============================================================
if "all_lessons" not in st.session_state:
    st.session_state.all_lessons = load_lessons()
    if not st.session_state.all_lessons:
        # 初回起動時のサンプル
        st.session_state.all_lessons = {
            "Smart Farming": {
                "title": "The Rise of Smart Farming",
                "text": "Smart farming uses IoT sensors and drones to monitor crop health. This technology helps farmers reduce water waste and optimize fertilizer use. In the future, AI will predict harvests with high accuracy.",
                "translation": "スマート農業は、作物の健康状態を監視するためにIoTセンサーやドローンを使用します。この技術は、農家が水の無駄を減らし、肥料の使用を最適化するのに役立ちます。将来的には、AIが高い精度で収穫を予測するようになるでしょう。",
                "vocab": [{"word": "optimize", "meaning": "最適化する"}, {"word": "fertilizer", "meaning": "肥料"}],
                "questions": [{"question": "What is used to monitor crop health?", "options": ["Drones", "Horses", "Manual labor"], "answer_index": 0, "explanation": "本文でIoTセンサーやドローンを使用すると述べられています。"}]
            }
        }

if "current_topic" not in st.session_state:
    st.session_state.current_topic = list(st.session_state.all_lessons.keys())[0]

# ============================================================
# 4. Gemini 3 ロジック
# ============================================================
def generate_lesson_gemini3(topic: str, level: str, api_key: str) -> dict:
    genai.configure(api_key=api_key)
    
    # システム指示（System Instruction）を分離して定義
    system_instruction = (
        "あなたは農業専門の英語教育者です。学習コンセプト『i+1』に基づき、"
        "指定されたレベル（英検）よりわずかに難しい単語を混ぜた教材を作成してください。"
        "レスポンスは必ず指定されたJSONフォーマットのみを返し、余計な解説は含めないでください。"
    )

    # モデルの初期化（※先ほどの無料枠の対応として 2.5 にしています）
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=system_instruction,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.7
        }
    )

    prompt = f"""
    以下の条件で英語レッスンを作成してください。
    - Topic: {topic}
    - Level: {level}
    - Text Length: 150-200 words
    - Content: タイトル, 本文, 日本語訳, 重要語彙(5つ), 3択クイズ(2問, 日本語解説付き)

    JSON Format:
    {{
      "title": "string",
      "text": "string",
      "translation": "string",
      "vocab": [{{ "word": "string", "meaning": "string" }}],
      "questions": [
        {{
          "question": "string",
          "options": ["string", "string", "string"],
          "answer_index": 0,
          "explanation": "日本語での解説"
        }}
      ]
    }}
    """

    response = model.generate_content(prompt)
    return json.loads(response.text)
# ============================================================
# 5. サイドバー
# ============================================================
with st.sidebar:
    st.title("⚙️ Controller")
    api_key = st.text_input("Gemini API Key:", type="password", help="Gemini 3 APIキーを入力してください")
    
    st.divider()
    st.subheader("New Lesson")
    new_topic = st.text_input("Topic:", placeholder="e.g., Organic Pest Control")
    level = st.selectbox("Target Level:", ["Eiken 3", "Eiken Pre-2", "Eiken 2", "Eiken Pre-1"])
    
    if st.button("✨ Generate with Gemini 3", use_container_width=True, type="primary"):
        if not api_key:
            st.warning("API Keyを入力してください。")
        elif not new_topic:
            st.warning("トピックを入力してください。")
        else:
            with st.spinner("Gemini 3 is thinking..."):
                try:
                    data = generate_lesson_gemini3(new_topic, level, api_key)
                    st.session_state.all_lessons[new_topic] = data
                    save_lessons(st.session_state.all_lessons)
                    st.session_state.current_topic = new_topic
                    st.success("Lesson generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    if st.button("🗑 Delete Lesson", use_container_width=True):
        if len(st.session_state.all_lessons) > 1:
            del st.session_state.all_lessons[st.session_state.current_topic]
            save_lessons(st.session_state.all_lessons)
            st.session_state.current_topic = list(st.session_state.all_lessons.keys())[0]
            st.rerun()

# ============================================================
# 6. メインUI
# ============================================================
st.title("🌱 AgriEnglish i+1")
st.caption("Agricultural English Learning powered by Gemini 3 Flash")

topics = list(st.session_state.all_lessons.keys())
selected_topic = st.selectbox("Lesson Select:", topics, index=topics.index(st.session_state.current_topic))

if selected_topic != st.session_state.current_topic:
    st.session_state.current_topic = selected_topic
    st.rerun()

data = st.session_state.all_lessons[selected_topic]

# 本文エリア
st.markdown(f"## {data.get('title', 'No Title')}")
st.components.v1.html(text_to_speech_js(data.get("text", "")), height=55)
st.markdown(f'<div class="reading-box">{data.get("text", "")}</div>', unsafe_allow_html=True)

# クイズエリア
st.subheader("📝 Comprehension Check")
questions = data.get("questions", [])

with st.form(key=f"quiz_{selected_topic}"):
    user_answers = []
    for i, q in enumerate(questions):
        st.write(f"**Q{i+1}: {q['question']}**")
        ans = st.radio("Select:", q['options'], key=f"opt_{selected_topic}_{i}")
        user_answers.append(ans)
        st.write("")
    
    submitted = st.form_submit_button("Check Answers")

if submitted:
    correct_total = 0
    for i, q in enumerate(questions):
        correct_ans = q['options'][q['answer_index']]
        if user_answers[i] == correct_ans:
            st.success(f"Q{i+1}: Correct! ✅")
            correct_total += 1
        else:
            st.error(f"Q{i+1}: Incorrect.")
        
        with st.expander(f"Q{i+1} Explanation"):
            st.write(f"**Correct Answer:** {correct_ans}")
            st.write(f"**Explanation:** {q.get('explanation')}")
            
    if correct_total == len(questions):
        st.balloons()

# サポートエリア
st.divider()
tab1, tab2 = st.tabs(["🇯🇵 Japanese Translation", "📖 Vocabulary"])

with tab1:
    st.info(data.get("translation", ""))

with tab2:
    for v in data.get("vocab", []):
        st.markdown(f"""<div class="vocab-card"><b>{v['word']}</b>: {v['meaning']}</div>""", unsafe_allow_html=True)