from flask import Flask, request, render_template
import os
import google.generativeai as genai

# Configure the Google Generative AI API
genai.configure(api_key=os.environ["API_KEY"])

app = Flask(__name__, template_folder="../templates")

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

@app.route("/", methods=["GET", "POST"])
def index():
    response_html = None  # Store the AI-generated HTML response
    if request.method == "POST":
        # Handle file upload
        if "image" in request.files:
            img = request.files["image"]
            img_path = os.path.join("uploads", img.filename)
            os.makedirs("uploads", exist_ok=True)
            img.save(img_path)

            # Upload to Gemini
            file = upload_to_gemini(img_path, mime_type="image/jpeg")

            # Create model instance
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                system_instruction="""
                You are an Instagram assistant specialized in creating engaging captions with relevant hashtags and recommending songs to enhance the mood of each photo. Every time I upload a photo, follow these steps:
                Generate Captions: Analyze the photo's content, mood, and setting. Based on this analysis, create 3-5 unique, creative captions for Instagram that reflect the visual elements or emotions in the image. Use a mix of descriptive language, emojis, and engaging phrases.
                Add Hashtags: With each caption, include 5-10 relevant hashtags to maximize visibility. Focus on popular and niche hashtags related to the photo's theme, location, or emotions.
                Suggest Songs: Suggest 5-10 songs that match the mood, theme, or setting of the photo. Include both classic and trending options if relevant, and choose songs that would resonate well as background music for social media posts. Aim for a variety that appeals to different tastes.
                Format the response in HTML as follows:
                Use <h2> for the section titles (e.g., "Captions", "Songs").
                List the captions inside <p> tags under the "Captions" section.
                Provide the song suggestions as another <ul> with <li> for each song under the "Songs" section.
                Respond in well-structured HTML format, making it easy to integrate directly into a webpage.
                """,
            )

            # Start a chat session with the uploaded file
            chat_session = model.start_chat(
                history=[{"role": "user", "parts": [file]}]
            )

            # Generate the AI response
            try:
                ai_response = chat_session.send_message("Don't send me response as a code block send response as a text/plain")
                response_html = ai_response.text  # The AI response should already be in HTML format
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response_html, "html.parser")
                captions = [p.text for p in soup.find_all("p")]
                songs = [li.text for li in soup.find_all("li")]
            except Exception as e:
                response_html = f"<p>Error: {str(e)}</p>"

    return render_template("index.html", response_html=response_html)

if __name__ == "__main__":
    app.run(port=4000,debug=True)
