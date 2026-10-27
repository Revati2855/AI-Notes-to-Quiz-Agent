# AI-Notes-to-Quiz-Agent
AI-powered learning assistant that generates study material and quizzes from PDF notes.

## Project Overview
AI Notes-to-Quiz Agent is an AI-powered learning application developed using Python and Streamlit. It allows students to upload PDF notes and uses the Gemini AI API to generate study material, interactive quizzes, and personalized practice questions.

## Objectives
- Generate summaries and important topics from PDF notes.
- Create MCQs, short-answer questions, and long-answer questions.
- Evaluate quiz answers and calculate scores.
- Identify weak topics based on incorrect answers.
- Generate personalized practice questions.
- Display scores and attempt history.

## Technologies Used
- Python
- Streamlit
- Gemini API
- google-genai
- pypdf
- python-dotenv
- JSON

## Main Features
1. PDF notes upload and text extraction.
2. AI-generated summaries and questions.
3. Interactive five-question MCQ quiz.
4. Automatic score calculation and answer explanations.
5. Weak-topic identification.
6. Personalized practice with three additional MCQs.
7. Performance dashboard and attempt-history table without a graph.

## Project Workflow
1. Upload PDF notes.
2. Extract text from the PDF.
3. Send the text to Gemini AI.
4. Display generated study material.
5. Generate and complete the interactive quiz.
6. Calculate scores and identify weak topics.
7. Generate personalized practice questions.
8. Display performance and attempt history.

## Installation and Setup
1. Install Python.
2. Create and activate a Python virtual environment.
3. Install the required packages:

```bash
pip install streamlit google-genai pypdf python-dotenv
```

4. Create a `.env` file in the project folder and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

Do not upload the `.env` file or your API key to GitHub.

## Run the Application

```bash
streamlit run app.py
```

## Limitations
- Internet access and a valid Gemini API key are required for AI generation.
- Scanned PDFs may require OCR support.
- Attempt history is stored in the current Streamlit session and may reset.

## Future Enhancements
- Permanent database storage for quiz history.
- OCR support for scanned PDFs.
- Different quiz difficulty levels.
- Downloadable study materials and performance reports.

