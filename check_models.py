"""Script to check available Gemini models and test which ones work"""

import config
import google.generativeai as genai

print("="*70)
print("🔍 Checking Available Gemini Models")
print("="*70)

# List all available models
print("\n📋 All Available Models:")
print("-" * 70)
try:
    models = genai.list_models()
    available_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')
            available_models.append(model_name)
            print(f"  ✅ {model_name}")
    
    print(f"\n📊 Total models with generateContent: {len(available_models)}")
    
    # Test some common model names
    print("\n" + "="*70)
    print("🧪 Testing Common Model Names")
    print("="*70)
    
    test_models = [
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-2.0-flash',
        'gemini-flash-latest',
        'gemini-pro-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
    ]
    
    working_models = []
    for model_name in test_models:
        try:
            print(f"\nTesting: {model_name}...", end=" ")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say hello in one word")
            if response.text:
                print(f"✅ WORKS - Response: {response.text[:50]}")
                working_models.append(model_name)
            else:
                print("❌ No response")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                print(f"❌ Not found")
            else:
                print(f"❌ Error: {error_msg[:80]}")
    
    print("\n" + "="*70)
    print("✅ Working Models:")
    print("="*70)
    if working_models:
        for model in working_models:
            print(f"  • {model}")
        print(f"\n💡 Recommended: {working_models[0]}")
    else:
        print("  ⚠️  No models tested successfully")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*70)

