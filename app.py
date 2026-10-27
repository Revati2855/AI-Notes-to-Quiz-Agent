import streamlit as st
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

# -------------------- PAGE SETTINGS --------------------

st.set_page_config(
    page_title="AI Notes-to-Quiz Agent",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Notes-to-Quiz Agent")
st.write(
    "Learn from your notes, test your knowledge, "
    "and improve with personalized practice."
)

# -------------------- GEMINI SETUP --------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL = "gemini-3.5-flash-lite"


# -------------------- AI HELPER FUNCTIONS --------------------

def generate_json(prompt):
    """Generate JSON content using Gemini."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    raw = (response.text or "").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)


def valid_questions(questions):
    """Check whether generated MCQs have the required structure."""

    if not isinstance(questions, list) or not questions:
        return False

    for q in questions:
        if not isinstance(q, dict):
            return False

        if not isinstance(q.get("question"), str):
            return False

        if not isinstance(q.get("options"), list):
            return False

        if len(q["options"]) != 4:
            return False

        if len(set(q["options"])) != 4:
            return False

        if q.get("answer") not in q["options"]:
            return False

        if not isinstance(q.get("topic"), str):
            return False

    return True


def add_history(attempt_type, score, total):
    """Record a completed quiz or practice attempt."""

    percentage = score / total * 100 if total else 0

    attempt_number = sum(
        item["Type"] == attempt_type
        for item in st.session_state.score_history
    ) + 1

    st.session_state.score_history.append({
        "Attempt": f"{attempt_type} {attempt_number}",
        "Type": attempt_type,
        "Score": score,
        "Total": total,
        "Percentage": round(percentage, 1)
    })


# -------------------- SESSION STATE --------------------

defaults = {
    "notes_text": "",
    "study_material": "",
    "quiz": [],
    "score": None,
    "weak_topics": [],
    "practice": [],
    "submitted_answers": [],
    "practice_score": None,
    "practice_submitted_answers": [],
    "score_history": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- PDF UPLOAD --------------------

st.header("📄 Step 1: Upload Your Notes")

uploaded_file = st.file_uploader(
    "Upload your study notes in PDF format",
    type=["pdf"]
)

if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("🔍 Analyze Notes"):
        try:
            with st.spinner("Extracting PDF text..."):
                reader = PdfReader(uploaded_file)
                text = ""

                for page in reader.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

            if not text.strip():
                st.error(
                    "No readable text found in this PDF. "
                    "Try a PDF containing selectable text."
                )

            else:
                st.session_state.notes_text = text

                # Reset results for the new notes.
                # Keep the previous attempt history.
                st.session_state.study_material = ""
                st.session_state.quiz = []
                st.session_state.score = None
                st.session_state.weak_topics = []
                st.session_state.practice = []
                st.session_state.submitted_answers = []
                st.session_state.practice_score = None
                st.session_state.practice_submitted_answers = []

                prompt = f"""
                Analyze these study notes and provide:

                1. A simple summary.
                2. Important topics.
                3. Five MCQs with four options each.
                4. Three short-answer questions with answers.
                5. Two long-answer questions with answers.

                Use simple, student-friendly language.
                Base the content only on the supplied notes.

                NOTES:
                {text[:25000]}
                """

                with st.spinner("Gemini is analyzing your notes..."):
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=prompt
                    )

                st.session_state.study_material = (
                    response.text or ""
                )

                if st.session_state.study_material:
                    st.success("Notes analyzed successfully!")

                else:
                    st.warning(
                        "The AI returned an empty response. "
                        "Please try again."
                    )

        except Exception as e:
            st.error(f"Analysis failed: {e}")


# -------------------- STUDY MATERIAL --------------------

if st.session_state.study_material:
    st.divider()
    st.header("🧠 Step 2: AI-Generated Study Material")
    st.markdown(st.session_state.study_material)


# -------------------- INTERACTIVE QUIZ --------------------

if st.session_state.study_material:
    st.divider()
    st.header("📝 Step 3: Interactive MCQ Quiz")

    if st.button("🎯 Generate Interactive Quiz"):
        try:
            quiz_prompt = f"""
            Create exactly 5 multiple-choice questions from these notes.

            Return ONLY a valid JSON array without Markdown fences.

            Each question must follow this structure:
            {{
                "question": "Question text",
                "topic": "Specific topic tested",
                "options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "answer": "Exact text of the correct option",
                "explanation": "Short explanation"
            }}

            Requirements:
            - Exactly five questions.
            - Four different options per question.
            - The answer must exactly match one option.
            - Assign a meaningful topic to every question.
            - Use only the supplied notes.

            NOTES:
            {st.session_state.notes_text[:25000]}
            """

            with st.spinner("Generating your quiz..."):
                quiz = generate_json(quiz_prompt)

            if len(quiz) != 5 or not valid_questions(quiz):
                raise ValueError(
                    "The generated quiz does not contain "
                    "exactly five valid questions."
                )

            st.session_state.quiz = quiz
            st.session_state.score = None
            st.session_state.weak_topics = []
            st.session_state.practice = []
            st.session_state.submitted_answers = []
            st.session_state.practice_score = None
            st.session_state.practice_submitted_answers = []

            st.success("Quiz generated successfully!")

        except Exception as e:
            st.error(f"Quiz generation failed: {e}")

    # -------------------- QUIZ FORM --------------------

    if st.session_state.quiz:
        with st.form("mcq_quiz"):
            answers = []

            for i, q in enumerate(st.session_state.quiz):
                st.markdown(f"**Q{i + 1}. {q['question']}**")

                selected = st.radio(
                    "Choose your answer:",
                    q["options"],
                    index=None,
                    key=f"answer_{i}"
                )

                answers.append(selected)

            submitted = st.form_submit_button("✅ Submit Quiz")

        if submitted:
            if any(answer is None for answer in answers):
                st.warning(
                    "Please answer every question before submitting."
                )

            else:
                score = sum(
                    answer == q["answer"]
                    for answer, q in zip(
                        answers, st.session_state.quiz
                    )
                )

                weak_topics = []

                for q, answer in zip(
                    st.session_state.quiz, answers
                ):
                    if answer != q["answer"]:
                        topic = q["topic"]

                        if topic not in weak_topics:
                            weak_topics.append(topic)

                st.session_state.score = score
                st.session_state.weak_topics = weak_topics
                st.session_state.submitted_answers = answers

                # Reset the current practice results.
                st.session_state.practice = []
                st.session_state.practice_score = None
                st.session_state.practice_submitted_answers = []

                # Record the completed quiz.
                add_history(
                    "Quiz",
                    score,
                    len(st.session_state.quiz)
                )

        # -------------------- QUIZ RESULTS --------------------

        if st.session_state.score is not None:
            st.divider()
            st.subheader("📊 Your Quiz Results")

            quiz_total = len(st.session_state.quiz)
            quiz_score = st.session_state.score

            quiz_percentage = (
                quiz_score / quiz_total * 100
                if quiz_total else 0
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Your Score",
                f"{quiz_score}/{quiz_total}"
            )

            col2.metric(
                "Quiz Accuracy",
                f"{quiz_percentage:.1f}%"
            )

            st.progress(int(quiz_percentage))

            for i, (q, answer) in enumerate(
                zip(
                    st.session_state.quiz,
                    st.session_state.submitted_answers
                )
            ):
                if answer == q["answer"]:
                    st.success(f"Q{i + 1}: Correct!")

                else:
                    st.error(f"Q{i + 1}: Incorrect")

                st.write(f"**Topic:** {q['topic']}")
                st.write(f"**Correct answer:** {q['answer']}")
                st.write(
                    f"**Explanation:** {q.get('explanation', '')}"
                )

            # -------------------- WEAK TOPICS --------------------

            st.divider()
            st.subheader("🎯 Weak-Topic Analysis")

            if st.session_state.weak_topics:
                st.write(
                    "These topics appeared in questions you "
                    "answered incorrectly. Practice them to improve."
                )

                for topic in st.session_state.weak_topics:
                    st.markdown(f"- 📌 {topic}")

                # -------------------- GENERATE PRACTICE --------------------

                if st.button("💡 Generate Personalized Practice"):
                    try:
                        topics = ", ".join(
                            st.session_state.weak_topics
                        )

                        practice_prompt = f"""
                        Create exactly 3 new multiple-choice questions
                        based on the student's weak topics.

                        Weak topics: {topics}

                        Use ONLY the supplied study notes.
                        Focus on understanding, not memorization alone.
                        Do not repeat the original quiz questions.

                        Return ONLY a valid JSON array without
                        Markdown fences.

                        Each question must follow this structure:
                        {{
                            "question": "Question text",
                            "topic": "Topic tested",
                            "options": [
                                "Option A",
                                "Option B",
                                "Option C",
                                "Option D"
                            ],
                            "answer": "Exact correct option",
                            "explanation": "Short explanation"
                        }}

                        NOTES:
                        {st.session_state.notes_text[:25000]}
                        """

                        with st.spinner(
                            "Generating personalized practice..."
                        ):
                            practice = generate_json(practice_prompt)

                        if (
                            len(practice) != 3
                            or not valid_questions(practice)
                        ):
                            raise ValueError(
                                "The practice questions have "
                                "an invalid format."
                            )

                        st.session_state.practice = practice
                        st.session_state.practice_score = None
                        st.session_state.practice_submitted_answers = []

                        st.success(
                            "Personalized practice generated!"
                        )

                    except Exception as e:
                        st.error(
                            f"Practice generation failed: {e}"
                        )

            else:
                st.success(
                    "Excellent! You answered every question "
                    "correctly. No weak topics were identified "
                    "in this quiz."
                )

            # -------------------- PRACTICE QUIZ --------------------

            if st.session_state.practice:
                st.divider()
                st.subheader("📚 Personalized Practice Questions")

                st.write(
                    "Answer these new questions based on "
                    "your weak topics."
                )

                with st.form("practice_quiz"):
                    practice_answers = []

                    for i, q in enumerate(st.session_state.practice):
                        st.markdown(
                            f"**Q{i + 1}. {q['question']}**"
                        )

                        selected = st.radio(
                            "Choose your answer:",
                            q["options"],
                            index=None,
                            key=f"practice_answer_{i}"
                        )

                        practice_answers.append(selected)

                    practice_submitted = st.form_submit_button(
                        "✅ Check Practice Answers"
                    )

                if practice_submitted:
                    if any(
                        answer is None
                        for answer in practice_answers
                    ):
                        st.warning(
                            "Please answer all practice questions."
                        )

                    else:
                        practice_score = sum(
                            answer == q["answer"]
                            for answer, q in zip(
                                practice_answers,
                                st.session_state.practice
                            )
                        )

                        st.session_state.practice_score = practice_score
                        st.session_state.practice_submitted_answers = (
                            practice_answers
                        )

                        # Record the completed practice attempt.
                        add_history(
                            "Practice",
                            practice_score,
                            len(st.session_state.practice)
                        )

                # -------------------- PRACTICE RESULTS --------------------

                if st.session_state.practice_score is not None:
                    practice_total = len(st.session_state.practice)
                    practice_score = st.session_state.practice_score

                    practice_percentage = (
                        practice_score / practice_total * 100
                        if practice_total else 0
                    )

                    st.subheader("📈 Practice Results")

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Practice Score",
                        f"{practice_score}/{practice_total}"
                    )

                    col2.metric(
                        "Practice Accuracy",
                        f"{practice_percentage:.1f}%"
                    )

                    st.progress(int(practice_percentage))

                    for i, (q, answer) in enumerate(
                        zip(
                            st.session_state.practice,
                            st.session_state.practice_submitted_answers
                        )
                    ):
                        if answer == q["answer"]:
                            st.success(f"Q{i + 1}: Correct!")

                        else:
                            st.error(f"Q{i + 1}: Incorrect")

                        st.write(f"**Topic:** {q['topic']}")
                        st.write(f"**Correct answer:** {q['answer']}")
                        st.write(
                            f"**Explanation:** "
                            f"{q.get('explanation', '')}"
                        )

                        st.divider()


# -------------------- PERFORMANCE DASHBOARD --------------------

st.divider()
st.header("📊 Performance Dashboard")

if st.session_state.score is not None:
    quiz_total = len(st.session_state.quiz)
    quiz_score = st.session_state.score

    quiz_percentage = (
        quiz_score / quiz_total * 100
        if quiz_total else 0
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Latest Quiz Score",
        f"{quiz_score}/{quiz_total}",
        f"{quiz_percentage:.1f}%"
    )

    if st.session_state.practice_score is not None:
        practice_total = len(st.session_state.practice)
        practice_score = st.session_state.practice_score

        practice_percentage = (
            practice_score / practice_total * 100
            if practice_total else 0
        )

        col2.metric(
            "Latest Practice Score",
            f"{practice_score}/{practice_total}",
            f"{practice_percentage:.1f}%"
        )

    else:
        col2.metric(
            "Latest Practice Score",
            "Not attempted"
        )

    st.subheader("📌 Topics to Revise")

    if st.session_state.weak_topics:
        for topic in st.session_state.weak_topics:
            st.write(f"- {topic}")

    else:
        st.success(
            "No weak topics identified in your latest quiz!"
        )

else:
    st.info(
        "Analyze your notes and complete a quiz "
        "to see your performance dashboard."
    )


# -------------------- ATTEMPT HISTORY --------------------

st.divider()
st.subheader("🧾 Performance History")

history = st.session_state.score_history

st.caption(f"Recorded attempts: {len(history)}")

if history:
    st.write("### Your Previous Attempts")

    # Show attempt history as a table without a graph.
    display_history = [
        {
            "Attempt": item["Attempt"],
            "Type": item["Type"],
            "Score": f'{item["Score"]}/{item["Total"]}',
            "Percentage": f'{item["Percentage"]:.1f}%'
        }
        for item in history
    ]

    st.table(display_history)

else:
    st.info(
        "No attempts recorded yet. Complete and submit a quiz "
        "to see your attempt history."
    )

st.caption(
    "Note: Attempt history is stored in the current Streamlit "
    "session. It may be cleared when the session resets."
)
