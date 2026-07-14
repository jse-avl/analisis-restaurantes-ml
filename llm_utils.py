"""Adaptador universal para multiples proveedores de LLM.
Soporta: Anthropic, OpenAI, Google Gemini, Groq.
Seleccion automatica segun API key disponible.
"""

import os
import hashlib
import time

CACHE_SIZE = 200
_last_call = {}


def _rate_limit(provider, min_interval=1.0):
    now = time.time()
    if provider in _last_call:
        elapsed = now - _last_call[provider]
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
    _last_call[provider] = time.time()


def _hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()


def _call_anthropic(prompt, system_prompt="", max_tokens=500):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        _rate_limit("anthropic")
        kwargs = {"model": "claude-3-haiku-20240307", "max_tokens": max_tokens}
        messages = []
        if system_prompt:
            kwargs["system"] = system_prompt
        messages.append({"role": "user", "content": prompt})
        kwargs["messages"] = messages
        resp = client.messages.create(**kwargs)
        return resp.content[0].text
    except Exception as e:
        return f"Error Anthropic: {e}"


def _call_openai(prompt, system_prompt="", max_tokens=500):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        _rate_limit("openai")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error OpenAI: {e}"


def _call_gemini(prompt, system_prompt="", max_tokens=500):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        _rate_limit("gemini")
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        resp = model.generate_content(full_prompt)
        return resp.text
    except Exception as e:
        return f"Error Gemini: {e}"


def _call_groq(prompt, system_prompt="", max_tokens=500):
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        _rate_limit("groq")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error Groq: {e}"


def get_available_provider():
    providers = [
        ("anthropic", os.getenv("ANTHROPIC_API_KEY"), _call_anthropic),
        ("openai", os.getenv("OPENAI_API_KEY"), _call_openai),
        ("gemini", os.getenv("GEMINI_API_KEY"), _call_gemini),
        ("groq", os.getenv("GROQ_API_KEY"), _call_groq),
    ]
    for name, key, func in providers:
        if key and key != "tu_api_key_aqui" and len(key) > 10:
            return name, func
    return None, None


def consultar_llm(prompt, system_prompt="", max_tokens=500, usar_cache=True):
    cache_key = _hash_text(prompt + system_prompt)
    if usar_cache and cache_key in consultar_llm._cache:
        return consultar_llm._cache[cache_key]

    provider_name, provider_func = get_available_provider()
    if not provider_func:
        return None

    result = provider_func(prompt, system_prompt, max_tokens)

    if usar_cache and result and not result.startswith("Error"):
        consultar_llm._cache[cache_key] = result
        if len(consultar_llm._cache) > CACHE_SIZE:
            consultar_llm._cache.clear()

    return result


consultar_llm._cache = {}


def generar_resumen_restaurante(restaurante, stats, num_resenas, sent_comida, sent_servicio, sent_precio):
    prompt = (
        f"Genera un resumen ejecutivo de 3 parrafos sobre el desempeno del restaurante '{restaurante}' "
        f"basado en los siguientes datos:\n"
        f"- Rating promedio: {stats.get('rating_promedio', 'N/A')}\n"
        f"- Total resenas: {num_resenas}\n"
        f"- Sentimiento comida: {sent_comida}\n"
        f"- Sentimiento servicio: {sent_servicio}\n"
        f"- Sentimiento precio: {sent_precio}\n"
        f"Destaca fortalezas, areas de mejora, y tendencias principales."
    )
    return consultar_llm(prompt,
                         system_prompt="Eres un analista de datos de restaurantes. Responde en espanol de forma clara y concisa.",
                         max_tokens=500)


def consultar_chat(pregunta, contexto_resumen):
    prompt = (
        f"Contexto actual de los datos de restaurantes:\n{contexto_resumen}\n\n"
        f"Pregunta del usuario: {pregunta}\n\n"
        f"Responde basandote exclusivamente en los datos proporcionados."
    )
    return consultar_llm(prompt,
                         system_prompt="Eres un asistente de analisis de restaurantes. Responde SOLO con informacion respaldada por los datos. Se conciso.",
                         max_tokens=600)
