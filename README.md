<!-- This is an HTML comment, which is invisible in the final rendered Markdown. -->
<!-- The line below uses a Level 1 Heading (#) and an emoji (:sparkles:) for the main title. -->
# ✨ Knowledge Quest: The AI-Powered Quiz Generator

<!-- This is a link to your app. Replace "#" with your actual Streamlit share URL. -->
[[Streamlit App]](#)

<!-- A short, bolded paragraph to grab attention. -->
Welcome to **Knowledge Quest**, your personal AI companion for learning! This app transforms any text—your study notes, articles, or even book chapters—into a fun and interactive quiz. Supercharge your study sessions, test your knowledge, and make learning an exciting adventure!

<!-- Placeholder for an image. It's highly recommended to add a screenshot or GIF of your app in action. -->
<!-- ![Knowledge Quest Demo](path/to/your/demo.gif) -->

<!-- Level 2 Heading (##) for a new section. -->
## 🚀 Live Demo

Ready to start your quest? Try the app live!

<!-- A bolded link to make the call-to-action stand out. -->
➡️ **[Launch Knowledge Quest](https://multiplechoicequiz.streamlit.app/)**

## 🌟 Key Features

<!-- An unordered list (-) to highlight the main features. Emojis make it more visually appealing. -->
- **🧠 AI-Powered Quiz Generation:** Simply paste any text, and our advanced AI will generate thoughtful questions and answers for you.
- **📚 Document Text Extraction:** Upload your documents (`.pdf`, `.docx`, `.txt`) and let the app extract the text automatically.
- **🤖 Customizable AI Settings:** Tailor your quiz by choosing your preferred AI model (like Gemini or GPT) and setting the exact number of questions you want.
- **✅ JSON Support:** Already have a quiz? You can paste a pre-formatted JSON array of questions to start immediately.
- **🎯 Interactive Quiz Interface:** Engage with a clean, step-by-step quiz format that makes learning feel like a game.
- **📈 Review & Summarize:** After the quiz, enter **Revision Mode** to review your answers and get a final performance summary to track your progress.

## 🕹️ How to Use

Getting started is as easy as 1-2-3!

<!-- An ordered list (1., 2., etc.) for step-by-step instructions. -->
1.  **Paste Your Content:** Copy your study material and paste it into the main text area.
2.  **Adjust Settings:** Open the "🤖 AI Generation Settings" to select your AI model and the number of questions.
3.  **Start the Quiz:** Click the **`🚀 Start Quiz`** button and let the magic happen!
4.  **Answer & Learn:** Progress through the questions and see how well you know your stuff.
5.  **Review:** Once finished, check the summary and review your answers to solidify your knowledge.

## 🛠️ Technical Stack

- **Framework:** [Streamlit](https://streamlit.io/)
- **Language:** Python
- **AI Models:** Gemini-2.5-Flash, Gemini-2.5-Pro, GPT-5-mini (via Poe API or similar)

## 💻 Setup and Local Installation

Want to run the app on your own machine? Follow these steps.

<!-- Level 3 Headings (###) for sub-sections. -->
### 1. Clone the Repository

<!-- A fenced code block with `bash` for syntax highlighting. -->
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```


### 2. Create a Virtual Environment
It's best practice to create a virtual environment to manage dependencies.

```bash
# For Mac/Linux
python3 -m venv venv
source venv/bin/activate
```


```bash
# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
install necesary libraries:

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

The app uses an AI client (init_poe_client()) which likely requires an API key. Create a file named .secrets in the root directory .\streamlit and add your key:
```
# .secrets
POE_API_KEY = "YOUR_POE_KEY_HERE"
[jsonbin]
api_key = "JSONBIN_API_KEY_HERE"
bin_id = "BIN_ID_HERE"
```

Your Python script should be configured to load this variable (e.g., using the python-dotenv library).

### 5. Run the App
You're all set! Launch the Streamlit app with this command:

```bash
streamlit run your_app_script.py
```

### 💡 Future Enhancements
Knowledge Quest is always growing! Here are some features planned for the future:

* 🔊 Audio Mode: An accessible, hands-free quiz experience with text-to-speech.
* ❓ More Question Types: Support for True/False and Fill-in-the-blanks.
* 👤 User Accounts: Save your quiz history and track performance over time.
* 🌐 Shareable Quizzes: Generate a unique link to share your quiz with friends.
* 🙌 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page or start a discussion.

---

Made with ❤️ and a passion for learning.