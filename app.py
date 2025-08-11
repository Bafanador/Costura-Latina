import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Para manejar CORS
from supabase import create_client, Client # Cliente de Supabase para Python
from dotenv import load_dotenv # Para cargar variables de entorno (solo para desarrollo local)

# Carga las variables de entorno del archivo .env si ejecutas localmente
# Render gestiona las variables de entorno directamente en su plataforma,
# por lo que esta línea no es estrictamente necesaria en producción.
load_dotenv()

# Inicializa la aplicación Flask
app = Flask(__name__)
# Configura CORS. En desarrollo, permitimos todos los orígenes.
# En producción, deberías restringir 'origins' a la URL específica de tu frontend.
CORS(app, origins="*", methods=["GET", "POST"], allow_headers=["Content-Type"])

# Configuración de las credenciales de Supabase
# Se cargan desde las variables de entorno (archivo .env o configuradas en Render)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Verifica que las credenciales estén configuradas
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Las variables de entorno SUPABASE_URL o SUPABASE_ANON_KEY no están configuradas.")
    exit(1) # Sale de la aplicación si faltan las credenciales

# Inicializa el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print(f"Conectado a Supabase en URL: {SUPABASE_URL}")

# Ruta para recibir las solicitudes de presupuesto
@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Asegúrate de que la solicitud sea JSON
    if not request.is_json:
        return jsonify({"message": "La solicitud debe ser JSON"}), 400

    # Extrae los datos del cuerpo de la solicitud JSON
    data = request.get_json()
    nombre = data.get('nombre')
    correo = data.get('correo')
    whatsapp = data.get('whatsapp')
    descripcion = data.get('descripcion')

    # Validación básica de los datos
    if not nombre or not descripcion:
        return jsonify({"message": "Nombre y descripción son campos obligatorios."}), 400

    try:
        # Inserta los datos en la tabla 'solicitudes_presupuesto' de Supabase
        # Asegúrate de que el nombre de la tabla coincida con el de tu base de datos
        response = supabase.table("solicitudes_presupuesto").insert(
            {
                "nombre": nombre,
                "correo": correo,
                "whatsapp": whatsapp,
                "descripcion": descripcion
            }
        ).execute()

        # Supabase devuelve el resultado de la operación en response.data
        if response.data:
            print(f"Datos insertados en Supabase: {response.data}")
            return jsonify({"message": "¡Tu solicitud ha sido enviada con éxito!", "data": response.data}), 200
        else:
            # Si no hay data pero tampoco error, podría ser una respuesta vacía o un problema inesperado
            print(f"Respuesta inesperada de Supabase: {response}")
            return jsonify({"message": "Error al insertar la solicitud en Supabase: Respuesta vacía."}), 500

    except Exception as e:
        print(f"Error al insertar en Supabase: {e}")
        return jsonify({"message": f"Error interno del servidor: {str(e)}"}), 500

# Punto de entrada para ejecutar la aplicación Flask
if __name__ == '__main__':
    # El puerto es manejado por Render automáticamente, pero localmente puedes usar 3000
    port = int(os.environ.get("PORT", 3000))
    app.run(debug=True, host='0.0.0.0', port=port)
