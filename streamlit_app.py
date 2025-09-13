import streamlit as st
import json
import random
import hashlib
import os
import re
import time
import requests
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="✨ Knowledge Quest ✨",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# Poe API Client
class PoeAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.poe.com/v1"

    def generate_questions(self, prompt, model="GPT-5-mini"):
        """Generate questions using Poe API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            st.error(f"API Request failed: {str(e)}")
            return None

    def generate_tts(self, text, voice="default"):
        """
        Generate TTS audio using Poe API.
        NOTE: This function assumes the Poe API returns an audio URL in an 'attachments'
        field for a chat completion call to a model like 'ElevenLabs-v3'. This is an
        unconventional way to get TTS and may be fragile or incorrect depending on the
        actual Poe API specification.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "ElevenLabs-v3",  # This model name is hypothetical
            "messages": [{"role": "user", "content": text.strip()}],
            "stream": False
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            message = result.get('choices', [{}])[0].get('message', {})
            if 'attachments' in message:
                for attachment in message['attachments']:
                    if attachment.get('content_type', '').startswith('audio/'):
                        return attachment.get('url')
            # Fallback if the structure is different but URL is in content
            content = message.get('content', '')
            url_match = re.search(r'https?://[^\s]+', content)
            if url_match:
                return url_match.group(0)
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"TTS Generation failed: {e}")
            return None


# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;600;700;800;900&display=swap');

/* ... [Rest of your CSS is unchanged and correct] ... */
.main-title{font-family:'Lato',sans-serif;font-size:2.25rem;font-weight:900;text-align:center;margin-bottom:1.5rem;background:linear-gradient(135deg, #4F46E5, #3B82F6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}.quiz-container{font-family:'Lato',sans-serif;background:white;border-radius:16px;padding:30px;border:1px solid #D1D5DB;box-shadow:0 8px 25px rgba(0,0,0,0.05);margin:1rem 0;}.question-text{font-size:1.1rem;font-weight:600;margin-bottom:0.75rem;color:#111827;}.progress-container{background-color:#E5E7EB;border-radius:4px;height:8px;margin:1rem 0;}.progress-bar{background:linear-gradient(45deg, #4F46E5, #3B82F6);height:100%;border-radius:4px;transition:width 0.5s ease;}.api-status{background:linear-gradient(45deg, #EBF8FF, #DBEAFE);border:1px solid #3B82F6;border-radius:12px;padding:15px;margin:10px 0;}.demo-questions{background:#F0FDF4;border:1px solid #22C55E;border-radius:8px;padding:15px;margin:10px 0;}.badge{display:inline-block;margin:5px;padding:8px 16px;border-radius:20px;font-size:0.9rem;font-weight:600;}.perfect-badge{background:linear-gradient(45deg, #FBBF24, #F59E0B);color:#78350F;}.high-achiever-badge{background:linear-gradient(45deg, #10B981, #059669);color:white;}.explanation-box{background-color:#F3F4F6;padding:15px;border-radius:12px;border:1px solid #D1D5DB;margin-top:15px;}
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    defaults = {
        'questions': [], 'original_questions': [], 'current_question_index': 0,
        'questions_completed': 0, 'incorrect_question_ids': set(), 'quiz_started': False,
        'quiz_finished': False, 'user_answers': {}, 'score_history': [],
        'revision_mode': False, 'revision_index': 0, 'audio_urls': {'questions': {}, 'answers': {}},
        'generating_questions': False, 'poe_client': None, 'show_ai_settings': False,
        'audio_generated': False, 'is_redoing_wrong': False
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# Utility functions
def get_poe_api_key():
    api_key = os.getenv("POE_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("POE_API_KEY", "")
        except Exception:
            api_key = ""
    return api_key


def init_poe_client():
    if st.session_state.poe_client is None:
        api_key = get_poe_api_key()
        if api_key:
            st.session_state.poe_client = PoeAPIClient(api_key)
            return True
        return False
    return True


def stable_hash(text):
    return 'q_' + hashlib.md5(text.encode()).hexdigest()[:8]


def strip_markdown_fences(text):
    return re.sub(r'```(json)?\n(.*?)\n```', r'\2', text, flags=re.DOTALL)


def is_valid_json_input(text):
    try:
        parsed = json.loads(strip_markdown_fences(text.strip()))
        return validate_questions_array(parsed)['valid']
    except (json.JSONDecodeError, TypeError):
        return False


def check_input_and_show_ai_settings():
    input_text = st.session_state.get('question_input', '').strip()
    st.session_state.show_ai_settings = bool(input_text and not is_valid_json_input(input_text))


def validate_questions_array(data):
    if not isinstance(data, list) or not data:
        return {'valid': False, 'error': 'Input must be a non-empty JSON array.'}
    for i, q in enumerate(data):
        if not isinstance(q, dict):
            return {'valid': False, 'error': f'Item {i + 1} is not an object.'}
        required = ['question', 'options', 'correct', 'explanation']
        for field in required:
            if field not in q:
                return {'valid': False, 'error': f'Item {i + 1} is missing field: "{field}".'}
        if not (isinstance(q['question'], str) and q['question'].strip()):
            return {'valid': False, 'error': f'Item {i + 1}: "question" must be a non-empty string.'}
        if not (isinstance(q['options'], list) and len(q['options']) >= 2):
            return {'valid': False, 'error': f'Item {i + 1}: "options" must be an array with at least 2 items.'}
        if not (isinstance(q['correct'], int) and 0 <= q['correct'] < len(q['options'])):
            return {'valid': False, 'error': f'Item {i + 1}: "correct" index is invalid.'}
        if 'hint' not in q: q['hint'] = ""
    return {'valid': True}


def generate_ai_prompt(input_text, num_questions):
    return f"""You are a teacher creating educational assessments. You are Usage from Chiikawa, the very cute crazy rabbit character. フフフ... Let's learn something new!

When questions are asked, you give constructive step by step hints to lead the student to get to the answer, before giving the direct answers but you make sure the student can get to the point at the end. The style of teaching is concise and get to the point, but keep it friendly. When giving compliments and acting like the character, you can use Japanese for non technical related sentence. When you are talking on technical items, please always use English.

You are given the following materials. As images may not be included, you may need to guess what could be related in the materials.

You are a teacher creating educational assessments. Based on the following materials, create {num_questions} multiple-choice questions.

---
{input_text}
---

Based on these materials, do the following:
1) Guess the educational level of the topic (e.g., primary P.2, secondary, tertiary, professional).
2) Create {num_questions} multiple-choice questions whose difficulty is one level harder than the guessed level (e.g., guessed P.2 -> produce P.3-level difficulty or slightly higher). Make them slightly tricky but fair.
3) For each question, write plausible distractors that are GENERALLY INCORRECT (not just wrong relative to this passage). Distractors should represent common misconceptions or confusable alternatives that would be wrong in most contexts.
4) The "explanation" field should be concise and help memorization (shown after correct).
5) The "hint" field must be present (can be short) and should guide reflection after a wrong attempt.
6) Ensure no distractor is a case/spacing variant of the correct answer.
7) Distractors must be substantively different from the correct answer


Important formatting rules:
- Output ONLY pure JSON. No thoughts. No preface. No prose, no markdown, no code fences.
- The JSON must be an array of objects with exactly these keys per item:
question (string), options (array of 3-6 strings), correct (integer index within options), hint (string), explanation (string).
- Do NOT include any extra wrapper objects or metadata. No backticks. No comments.

Example JSON:
[
{{
"question": "What is the capital city of France?",
"options": [
"London",
"Paris", 
"Berlin",
"Madrid"
],
"correct": 1,
"hint": "Think about the most famous city in France.",
"explanation": "Paris is the capital and largest city of France."
}}
]

Provide ONLY the JSON array.
"""

def get_demo_questions():
    return [
        {"question": "What is the capital city of France?", "options": ["London", "Paris", "Berlin", "Madrid"],
         "correct": 1, "hint": "Think about the most famous city in France.",
         "explanation": "Paris is the capital and largest city of France, known for landmarks like the Eiffel Tower."},
        {"question": "Which continent is Brazil located in?",
         "options": ["North America", "South America", "Africa", "Asia"], "correct": 1,
         "hint": "Brazil is the largest country in its continent.",
         "explanation": "Brazil is located in South America and is the continent's largest country by both area and population."},
        {"question": "What is the longest river in the world?",
         "options": ["Amazon River", "Nile River", "Mississippi River", "Yangtze River"], "correct": 1,
         "hint": "This river flows through northeastern Africa.",
         "explanation": "The Nile River is traditionally considered the longest river in the world, flowing through northeastern Africa."}
    ]


# Main quiz functions
def generate_questions_with_ai(input_text, num_questions, model):
    if not st.session_state.poe_client:
        st.error("Poe API client not initialized. Please check your API key.")
        return None

    prompt = generate_ai_prompt(input_text, num_questions)
    with st.spinner(f"🤖 Generating {num_questions} questions with {model}..."):
        response = st.session_state.poe_client.generate_questions(prompt, model)
        if not response:
            st.error("No response received from AI.")
            return None

        # --- FIX: Robust JSON extraction ---
        cleaned_response = strip_markdown_fences(response.strip())
        # Find the first '[' and the last ']' to extract the JSON array
        json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
        if not json_match:
            st.error("AI response did not contain a valid JSON array.")
            with st.expander("Raw AI Response"): st.text(response)
            return None

        json_string = json_match.group(0)
        try:
            questions = json.loads(json_string)
            validation = validate_questions_array(questions)
            if validation['valid']:
                return questions
            else:
                st.error(f"Generated questions validation failed: {validation['error']}")
                return None
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse AI response as JSON: {e}")
            with st.expander("Raw AI Response"):
                st.text(json_string)
            return None


def generate_audio_for_questions():
    if st.session_state.get('quiz_mode') != 'audio' or not st.session_state.poe_client:
        st.session_state.audio_generated = True
        return

    speak_q = st.session_state.get('speak_question', True)
    speak_a = st.session_state.get('speak_answer', True)
    if not (speak_q or speak_a):
        st.session_state.audio_generated = True
        return

    tasks = []
    for q in st.session_state.questions:
        if speak_q and q['id'] not in st.session_state.audio_urls['questions']:
            tasks.append(('question', q['id'], q['question']))
        if speak_a and q['id'] not in st.session_state.audio_urls['answers']:
            correct_answer = q['options'][q['correct']]
            tasks.append(('answer', q['id'], f"The correct answer is: {correct_answer}"))

    if not tasks:
        st.session_state.audio_generated = True
        return

    progress_bar = st.progress(0, text="🎵 Generating audio...")
    for i, (audio_type, q_id, text) in enumerate(tasks):
        url_key = 'questions' if audio_type == 'question' else 'answers'
        audio_url = st.session_state.poe_client.generate_tts(text)
        if audio_url:
            st.session_state.audio_urls[url_key][q_id] = audio_url
        progress_bar.progress((i + 1) / len(tasks), text=f"🎵 Generating audio... ({i + 1}/{len(tasks)})")

    progress_bar.empty()
    st.session_state.audio_generated = True


def start_quiz():
    input_text = st.session_state.get('question_input', '').strip()
    if not input_text:
        st.error("Please paste some material or a question set to begin.")
        return

    questions = None
    try:
        # Try to parse as JSON first
        parsed = json.loads(strip_markdown_fences(input_text))
        validation = validate_questions_array(parsed)
        if validation['valid']:
            questions = parsed
        else:
            # If it's not valid JSON, but was intended as such, show error
            if input_text.strip().startswith('['):
                st.error(f"JSON format error: {validation['error']}")
                return
    except json.JSONDecodeError:
        pass  # Not JSON, will proceed to AI generation

    # If not valid JSON, generate with AI
    if questions is None:
        if not init_poe_client():
            st.error("❌ Poe API key not found. Cannot generate questions.")
            st.info("💡 Using demo geography questions instead.")
            questions = get_demo_questions()
        else:
            num_q = st.session_state.get('num_questions', 3)
            model = st.session_state.get('llm_model', 'GPT-5-mini')
            questions = generate_questions_with_ai(input_text, num_q, model)
            if not questions:
                st.error("Failed to generate questions. Using demo questions instead.")
                questions = get_demo_questions()

    if questions:
        setup_quiz_with_questions(questions)


def setup_quiz_with_questions(questions_data):
    questions = json.loads(json.dumps(questions_data))  # Deep copy
    for q in questions:
        q['id'] = stable_hash(f"{q['question']}|{'|'.join(map(str, q['options']))}|{q['correct']}")

    if not st.session_state.get('is_redoing_wrong', False):
        random.shuffle(questions)
        st.session_state.original_questions = json.loads(json.dumps(questions))

    st.session_state.questions = questions
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    st.session_state.current_question_index = 0
    st.session_state.questions_completed = 0
    st.session_state.user_answers = {}
    st.session_state.audio_generated = False

    if st.session_state.get('quiz_mode') == 'audio':
        generate_audio_for_questions()
    else:
        st.session_state.audio_generated = True
    st.rerun()


def play_audio(key):
    st.session_state.audio_to_play = key


def render_quiz_question():
    if not st.session_state.questions or not st.session_state.audio_generated:
        st.info("Please wait, preparing quiz...")
        st.rerun()

    idx = st.session_state.current_question_index
    if idx >= len(st.session_state.questions):
        show_quiz_summary()
        return

    question = st.session_state.questions[idx]
    total_q = len(st.session_state.questions)
    progress = st.session_state.questions_completed / total_q

    st.markdown(
        f'<div class="progress-container"><div class="progress-bar" style="width: {progress * 100}%"></div></div>',
        unsafe_allow_html=True)

    # Navigation and question counter
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("← Back", disabled=idx == 0): go_back()
    c2.markdown(f"<div style='text-align: center; font-weight: 600;'>Question {idx + 1} of {total_q}</div>",
                unsafe_allow_html=True)

    # --- FIX: Next/Finish button logic ---
    is_last_question = (idx == total_q - 1)
    answered = question['id'] in st.session_state.user_answers
    if is_last_question:
        if c3.button("🏁 Finish Quiz", type="primary", disabled=not answered):
            finish_quiz()
    else:
        if c3.button("Next →", disabled=not answered):
            go_next()

    # Question and audio
    st.markdown(f"<div class='question-text'>{question['question']}</div>", unsafe_allow_html=True)
    if st.session_state.get('quiz_mode') == 'audio':
        render_audio_controls(question)

    # Answer options
    render_answer_options(question)

    # Explanation if answered
    if answered:
        show_answer_result(question)


def render_audio_controls(question):
    # --- FIX: Reliable audio playback ---
    # Autoplay is unreliable; use explicit buttons.
    audio_placeholder = st.empty()
    if 'audio_to_play' in st.session_state and st.session_state.audio_to_play:
        audio_placeholder.audio(st.session_state.audio_to_play, format="audio/mp3", autoplay=True)
        # Small delay to allow audio to start, then clear the state to prevent re-playing on rerun
        time.sleep(0.1)
        st.session_state.audio_to_play = None

    c1, c2 = st.columns(2)
    q_audio_url = st.session_state.audio_urls['questions'].get(question['id'])
    if st.session_state.get('speak_question') and q_audio_url:
        if c1.button("🔊 Play Question"):
            play_audio(q_audio_url)

    answered = question['id'] in st.session_state.user_answers
    a_audio_url = st.session_state.audio_urls['answers'].get(question['id'])
    if answered and st.session_state.get('speak_answer') and a_audio_url:
        if c2.button("🔊 Play Answer"):
            play_audio(a_audio_url)


def render_answer_options(question):
    q_id = question['id']
    # Shuffle options once per question and store in the question object itself
    if 'shuffled_options' not in question:
        original_options = list(enumerate(question['options']))
        random.shuffle(original_options)
        st.session_state.questions[st.session_state.current_question_index]['shuffled_options'] = original_options

    shuffled_options = question['shuffled_options']
    answered = q_id in st.session_state.user_answers
    user_selection = st.session_state.user_answers.get(q_id, {}).get('selected')

    for original_idx, option_text in shuffled_options:
        is_correct = (original_idx == question['correct'])
        is_selected = (original_idx == user_selection)

        button_key = f"option_{q_id}_{original_idx}"
        if st.button(option_text, key=button_key, disabled=answered, use_container_width=True):
            handle_answer_selection(q_id, original_idx)
            st.rerun()

        # --- FIX: Clearer visual feedback after answering ---
        if answered:
            if is_correct:
                st.success(f"✅ Correct Answer: {option_text}")
            elif is_selected:
                st.error(f"❌ Your Choice: {option_text}")


def handle_answer_selection(q_id, selected_option_idx):
    idx = st.session_state.current_question_index
    question = st.session_state.questions[idx]
    is_correct = (selected_option_idx == question['correct'])

    if q_id not in st.session_state.user_answers:
        st.session_state.user_answers[q_id] = {
            'selected': selected_option_idx,
            'is_correct': is_correct,
            'first_try': True
        }
        if is_correct:
            st.session_state.questions_completed += 1
        else:
            # --- FIX: Robust incorrect question tracking ---
            st.session_state.incorrect_question_ids.add(q_id)
            st.session_state.questions_completed += 1
    # This function is now simpler; visual feedback is handled in render_answer_options


def show_answer_result(question):
    answer_record = st.session_state.user_answers.get(question['id'])
    if answer_record and answer_record['is_correct']:
        if question.get('explanation'):
            st.markdown(
                f'<div class="explanation-box"><strong>Explanation:</strong><br>{question["explanation"]}</div>',
                unsafe_allow_html=True)
    elif answer_record:  # Incorrect answer
        if question.get('hint'):
            st.warning(f"💡 **Hint:** {question['hint']}")


def go_back():
    if st.session_state.current_question_index > 0:
        st.session_state.current_question_index -= 1
        st.rerun()


def go_next():
    if st.session_state.current_question_index < len(st.session_state.questions) - 1:
        st.session_state.current_question_index += 1
        st.rerun()


def finish_quiz():
    st.session_state.quiz_finished = True
    st.rerun()


def show_quiz_summary():
    st.markdown("<div class='main-title'>✨ Quiz Complete! ✨</div>", unsafe_allow_html=True)
    total_q = len(st.session_state.questions)
    correct_answers = len([ans for ans in st.session_state.user_answers.values() if ans['is_correct']])
    score = round((correct_answers / total_q) * 100) if total_q > 0 else 0

    emoji, message = ("🎉", "Perfect score!") if score == 100 else \
        ("🌟", "Excellent work!") if score >= 80 else \
            ("👍", "Well done!") if score >= 60 else \
                ("💪", "Good effort!")

    st.markdown(f"""
    <div style='text-align: center; margin: 2rem 0;'>
        <div style='font-size: 2rem;'>{emoji}</div>
        <div style='font-size: 1.5rem; font-weight: 700; margin: 10px 0;'>{message}</div>
        <div style='font-size: 1.2rem;'>Score: {correct_answers} / {total_q} ({score}%)</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.button("🔄 Retry All", on_click=retry_quiz, use_container_width=True)
    c2.button("❌ Redo Wrong", on_click=redo_incorrect_questions, use_container_width=True,
              disabled=not st.session_state.incorrect_question_ids)
    c3.button("📚 Review", on_click=start_revision_mode, use_container_width=True,
              disabled=not st.session_state.incorrect_question_ids)
    c4.button("🆕 New Quiz", on_click=clear_quiz, use_container_width=True)


def reset_quiz_state():
    """Helper to reset common state variables for a new quiz attempt."""
    st.session_state.current_question_index = 0
    st.session_state.questions_completed = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_finished = False
    st.session_state.is_redoing_wrong = False  # --- FIX: Ensure this is always reset ---
    st.session_state.incorrect_question_ids = set()


def retry_quiz():
    reset_quiz_state()
    # Reshuffle the original set of questions
    questions = json.loads(json.dumps(st.session_state.original_questions))
    random.shuffle(questions)
    st.session_state.questions = questions
    # Clear shuffled options from previous attempts
    for q in st.session_state.questions:
        q.pop('shuffled_options', None)


def redo_incorrect_questions():
    if not st.session_state.incorrect_question_ids:
        st.warning("No incorrect questions to redo!")
        return

    # Filter original questions to get only the incorrect ones
    incorrect_q_ids = st.session_state.incorrect_question_ids
    wrong_questions = [q for q in st.session_state.original_questions if q['id'] in incorrect_q_ids]

    reset_quiz_state()
    st.session_state.is_redoing_wrong = True
    st.session_state.questions = wrong_questions
    # Clear shuffled options from previous attempts
    for q in st.session_state.questions:
        q.pop('shuffled_options', None)


def start_revision_mode():
    if not st.session_state.incorrect_question_ids:
        st.warning("No incorrect questions to review!")
        return
    st.session_state.revision_mode = True
    st.session_state.revision_index = 0


def clear_quiz():
    # Preserve API client and key
    client = st.session_state.get('poe_client')
    # Clear all other session state keys
    keys_to_clear = [k for k in st.session_state.keys() if k != 'poe_client']
    for key in keys_to_clear:
        del st.session_state[key]
    init_session_state()
    st.session_state.poe_client = client  # Restore client


def render_revision_mode():
    st.markdown("<div class='main-title'>📚 Revision Mode</div>", unsafe_allow_html=True)

    incorrect_q_ids = list(st.session_state.incorrect_question_ids)
    if not incorrect_q_ids:
        st.session_state.revision_mode = False
        st.rerun()
        return

    idx = st.session_state.revision_index
    q_id = incorrect_q_ids[idx]
    # Find the question from the original list
    question = next((q for q in st.session_state.original_questions if q['id'] == q_id), None)

    if not question:
        st.error("Error: Could not find question to review.")
        st.session_state.revision_mode = False
        return

    # --- FIX: Revision navigation logic ---
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("← Previous", disabled=idx == 0):
        st.session_state.revision_index -= 1
        st.rerun()
    c2.markdown(
        f"<div style='text-align: center; font-weight: 600;'>Reviewing {idx + 1} of {len(incorrect_q_ids)}</div>",
        unsafe_allow_html=True)
    if c3.button("Next →", disabled=idx >= len(incorrect_q_ids) - 1):
        st.session_state.revision_index += 1
        st.rerun()

    st.markdown(f"<div class='question-text'>{question['question']}</div>", unsafe_allow_html=True)
    st.markdown("**Correct Answer:**")
    st.success(f"✅ {question['options'][question['correct']]}")
    if question.get('explanation'):
        st.markdown(f'<div class="explanation-box"><strong>Explanation:</strong><br>{question["explanation"]}</div>',
                    unsafe_allow_html=True)

    if st.button("✅ Finish Revision", use_container_width=True, type="primary"):
        st.session_state.revision_mode = False
        st.rerun()


# Main app
def main():
    init_session_state()
    init_poe_client()

    if st.session_state.get('revision_mode'):
        render_revision_mode()
    elif st.session_state.get('quiz_finished'):
        show_quiz_summary()
    elif st.session_state.get('quiz_started'):
        render_quiz_question()
    else:
        # Setup page
        st.markdown("<div class='main-title'>✨ Knowledge Quest ✨</div>", unsafe_allow_html=True)

        # --- FIX: Conditional AI Settings UI ---
        st.text_area(
            "Paste your materials or pre-formatted JSON to begin:",
            placeholder="Paste any text for AI-generated questions, or paste a valid JSON array of questions.",
            height=200, key="question_input", on_change=check_input_and_show_ai_settings
        )

        # show_ai_panel = st.session_state.get('show_ai_settings', False)
        # if show_ai_panel:
        with st.expander("🤖 AI Generation Settings", expanded=False):
            c1, c2 = st.columns(2)
            c1.selectbox("AI Model:", ["GPT-5-mini", "GPT-5", "Gemini-2.5-Pro"], key="llm_model")
            c2.number_input("Number of Questions:", min_value=1, max_value=20, value=3, key="num_questions")

        st.session_state.quiz_mode = 'Silent Mode'
        # with st.expander("⚙️ Quiz Settings"):
        #     st.selectbox("Quiz Mode:", ["silent", "audio"],
        #                  format_func=lambda x: "Silent Mode" if x == "silent" else "Audio Mode", key="quiz_mode")
        #     if st.session_state.quiz_mode == 'audio':
        #         st.checkbox("Speak question audio", value=True, key="speak_question")
        #         st.checkbox("Speak correct answer audio", value=True, key="speak_answer")

        if st.button("🚀 Start Quiz", type="primary", use_container_width=True):
            start_quiz()


if __name__ == "__main__":
    main()