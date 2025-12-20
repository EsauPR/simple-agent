import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


def test_openai_api_key():
    """Prueba si la API key de OpenAI funciona correctamente."""
    # Cargar variables de entorno desde .env
    load_dotenv()

    # Obtener la API key desde variable de entorno
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Error: No se encontró la variable de entorno OPENAI_API_KEY")
        print("   Por favor, configura tu API key en el archivo .env:")
        print("   OPENAI_API_KEY=tu-api-key-aqui")
        print("   O como variable de entorno:")
        print("   export OPENAI_API_KEY='tu-api-key-aqui'")
        sys.exit(1)

    print("🔑 API Key encontrada")
    print("🧪 Probando conexión con OpenAI...")

    try:
        # Crear cliente de OpenAI
        client = OpenAI(api_key=api_key)

        # Hacer una llamada simple para listar modelos (es gratis y rápido)
        print("📡 Haciendo llamada de prueba...")
        models = client.models.list()

        print("✅ ¡Éxito! Tu API key de OpenAI funciona correctamente")
        print(f"   Se encontraron {len(list(models.data))} modelos disponibles")

        # Opcional: hacer una llamada de chat simple para verificar completamente
        print("\n🧪 Probando una llamada de chat simple...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Responde solo con 'OK' si puedes leer esto."}
            ],
            max_tokens=10
        )

        print(f"✅ Chat completado: {response.choices[0].message.content.strip()}")
        print("\n🎉 ¡Todo funciona perfectamente!")

    except Exception as e:
        print(f"❌ Error al conectar con OpenAI: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        sys.exit(1)


def main():
    test_openai_api_key()


if __name__ == "__main__":
    main()
