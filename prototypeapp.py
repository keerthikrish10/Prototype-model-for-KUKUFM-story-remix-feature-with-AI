import google.generativeai as genai
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import json
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 40,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Mock database
stories_db = {
    "story_001": {
        "title": "The Midnight Detective",
        "content": "Detective Roy was on the trail of the infamous jewel thief. As he followed the clues to the abandoned warehouse, he knew this could be his final case...",
        "default_ending": "Little did he know, his partner had betrayed him. As he entered the warehouse, a gunshot rang out, and Detective Roy fell to the ground, left for dead.",
        "genre": "mystery",
        "characters": {
            "protagonist": {"name": "Detective Roy", "gender": "male"},
            "sidekick": {"name": "Officer Lena", "gender": "female"}
        }
    }
}

user_preferences = {}
remix_history = {}

# Helper function to generate remix
def generate_story_remix(story_id, modifications):
    story = stories_db[story_id]
    prompt = f"""
    Original Story: {story['content']}
    Original Ending: {story['default_ending']}
    
    Modify this story with the following changes:
    - Genre: {modifications.get('genre', story['genre'])}
    - Ending: {modifications.get('ending', 'default')}
    - Character changes: {modifications.get('characters', 'none')}
    - Tone: {modifications.get('tone', 'default')}
    
    Provide:
    1. A rewritten version of the story with these modifications
    2. A new ending that matches the requested style
    3. Keep the core plot intact but adapt the style and details
    """
    
    response = model.generate_content(prompt)
    return response.text

# API Endpoints
@app.route('/api/stories/featured', methods=['GET'])
def get_featured_stories():
    """Endpoint for homepage with remix highlights"""
    return jsonify({
        "remix_of_the_day": {
            "story_id": "story_001",
            "title": "The Midnight Detective (Happy Ending Remix)",
            "description": "Experience this classic mystery with a heartwarming twist"
        },
        "trending_remixes": [
            {
                "story_id": "story_001",
                "title": "The Midnight Detective (Noir Version)",
                "likes": 142
            }
        ]
    })

@app.route('/api/stories/<story_id>', methods=['GET'])
def get_story(story_id):
    """Get story details and available remix options"""
    story = stories_db.get(story_id)
    if not story:
        return jsonify({"error": "Story not found"}), 404
    
    return jsonify({
        "story": story,
        "remix_options": {
            "genre": ["mystery", "comedy", "drama", "noir"],
            "ending": ["happy", "tragic", "twist", "open-ended"],
            "characters": ["swap genders", "change protagonist"],
            "tone": ["suspenseful", "humorous", "dramatic", "casual"]
        }
    })

@app.route('/api/remix', methods=['POST'])
def create_remix():
    """Generate a remixed version of a story"""
    data = request.json
    story_id = data.get('story_id')
    modifications = data.get('modifications', {})
    
    if not story_id or story_id not in stories_db:
        return jsonify({"error": "Invalid story ID"}), 400
    
    # Generate remix (in production, this would be async with webhooks)
    start_time = time.time()
    remix_content = generate_story_remix(story_id, modifications)
    generation_time = time.time() - start_time
    
    # Store remix history
    remix_id = f"remix_{int(time.time())}"
    remix_history[remix_id] = {
        "story_id": story_id,
        "modifications": modifications,
        "content": remix_content,
        "created_at": datetime.utcnow().isoformat(),
        "generation_time": generation_time
    }
    
    return jsonify({
        "remix_id": remix_id,
        "content": remix_content,
        "generation_time": generation_time
    })

@app.route('/api/remix/<remix_id>/feedback', methods=['POST'])
def submit_feedback(remix_id):
    """Record user feedback on a remix"""
    if remix_id not in remix_history:
        return jsonify({"error": "Remix not found"}), 404
    
    data = request.json
    rating = data.get('rating')  # 1-5 scale
    feedback = data.get('feedback', '')
    
    # In production, store this in a proper database
    remix_history[remix_id]['feedback'] = {
        "rating": rating,
        "comments": feedback
    }
    
    return jsonify({"status": "feedback recorded"})

if __name__ == '__main__':
    app.run(debug=True)