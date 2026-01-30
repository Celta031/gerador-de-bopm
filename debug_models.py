import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    print("\n--- TENTANDO LISTAR MODELOS ---")
    for m in client.models.list():
        name = getattr(m, 'name', 'Nome não encontrado')
        display = getattr(m, 'display_name', '')
        print(f"- {name} ({display})")
        
except Exception as e:
    print(f"\nERRO CRÍTICO: {e}")
    print("Verifique sua conexão de internet ou Proxy.")