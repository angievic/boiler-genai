import base64
import json
from llm_utils import call_llm, call_llm_to_generate_image
from typing import List
import streamlit as st
from moviepy import *
from gtts import gTTS
import os
import tempfile

def generate_copy_for_video(prompt: str, age_group: str) -> str:
    prompt = f"""
    You are a helpful, respectful and honest educational assistant.
    You will generate a script for an educational video.
    The script will be about the following topic:
    {prompt}
    Steps:
    1. Generate a script of 100 words or less having a good flow and language according to the age group {age_group} years old.
    2. Rewrite the script divided into 5 scenes. If a scene need more words to have a good flow, add it a maximun of 10 extra words.
    3. Return the script in a JSON format like this:
    {{
        "scenes": [
            {{
                "scene_number": 1,
                "scene_description": "Scene 1 description",
                "script": "Scene 1 script"
            }}
        ]
    }}
    """
    response = call_llm(prompt)
    return json.loads(response)

def generate_images_for_video(scenes: str, age_group: str) -> List[str]:
    images_decoded_base64 = []
    for scene in scenes:
        prompt = f"""
        You are an expert educational illustrator. 
        Create a detailed and engaging image for an educational video aimed at children aged {age_group} years old.

        Topic for the image:
        {scene["script"][:200]}

        Guidelines:
        - Use a unique, vibrant background color (avoid white).
        - The image should be clear, age-appropriate, and visually appealing for the specified age group.
        - Include no more than 5 distinct, relevant elements that directly illustrate the topic.
        - Exclude any logos, watermarks, backgrounds, borders, frames, or abstract elements not directly related to the scene.
        - Avoid text in the image.
        - Focus on clarity, simplicity, and educational value.

        Return only the image, with no additional text or explanation.
        """
        image_base64 = call_llm_to_generate_image(prompt)
        image_bytes = base64.b64decode(image_base64)
        images_decoded_base64.append({
            "scene_number": scene["scene_number"],
            "image_bytes": image_bytes
        })
    return images_decoded_base64

def create_video_from_scenes(scenes, output_path="output_video.mp4", duration=10, font_size=40, font_color='white'):
    clips = []
    temp_files = []

    try:
        for i, scene in enumerate(scenes):
            # Save image bytes to a temporary file
            img_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img_temp.write(scene["image_bytes"])
            img_temp.close()
            temp_files.append(img_temp.name)

            # Generate voice-over
            tts = gTTS(text=scene["script"], lang='en')
            audio_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(audio_temp.name)
            audio_temp.close()
            temp_files.append(audio_temp.name)
            audio_clip = AudioFileClip(audio_temp.name)

            # Create image and text clips
            img_clip = ImageClip(img_temp.name).with_duration(audio_clip.duration)
            txt_clip = TextClip(text=scene["scene_description"], color=font_color, font="./DejaVuSans.ttf", method='caption', size=img_clip.size).with_duration(audio_clip.duration).with_position('bottom', 150)

            # Overlay text on image
            video_clip = CompositeVideoClip([img_clip, txt_clip])

            # Add audio
            video_clip = video_clip.with_audio(audio_clip)

            clips.append(video_clip)

        # Concatenate all scene clips
        final_clip = concatenate_videoclips(clips,method="compose")
        final_clip.write_videofile(output_path, fps=24)

    finally:
        # Cleanup temp files
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)

    print(f"Video saved to {output_path}")

prompt = st.text_input('Enter the prompt for the educational video')
age_group = st.selectbox('Select the age group for the educational video', ['0-3', '3-6', '6-12', '12-18'])
if st.button('Generate Educational Video'):
    if prompt and age_group:
        video_text = generate_copy_for_video(prompt, age_group)
        #st.json(video_text)
        scenes = video_text["scenes"]
        images_decoded_base64 = generate_images_for_video(scenes, age_group)
        #for image in images_decoded_base64:
        #    st.image(image["image_bytes"])

        for scene in scenes:
            scene["image_bytes"] = images_decoded_base64[scene["scene_number"] - 1]["image_bytes"]
        create_video_from_scenes(scenes)
        