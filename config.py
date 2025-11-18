"""Configuration for KYC Multi-Agent System"""

import os
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDL96k-Rt8kbLpR7JnSZFzSRI3QptNgF7o")

if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️  Warning: GEMINI_API_KEY not set. Set it as environment variable or update config.py")

