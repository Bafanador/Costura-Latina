import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Para manejar CORS
import psycopg2 # Cliente de PostgreSQL para Python
from dotenv import load_dotenv # Para cargar variables de entorno (para desarrollo local)

# Carga las variables de entorno del archivo .env si ejecutas localmente
# En un entorno de producción, configurarías estas variables directamente en tu hosting.
load_dotenv()

# Inicializa la aplicación Flask
app = Flask(__name__)
# Configura CORS. En desarrollo, permitimos todos los orígenes.
# En producción, deberías restringir 'origins' a la URL específica de tu frontend.
CORS(app, origins="*", methods=["GET", "POST"], allow_headers=["Content-Type"])

# Configuración de las credenciales de la base de datos local PostgreSQL
# Se pueden cargar de variables de entorno (para producción) o usar valores por defecto (para local)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "solicitudes_presupuesto") # O el nombre de tu base de datos si es diferente
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Multielevacion1234")

# Función para establecer la conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos local: {e}")
        return None

print(f"La aplicación Flask está lista para conectarse a la base de datos local en {DB_HOST}:{DB_PORT}/{DB_NAME}")

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

    conn = None # Inicializar conn para asegurar que siempre esté definido
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Error interno del servidor: Fallo en la conexión a la base de datos local."}), 500

        cur = conn.cursor()

        # Inserta los datos en la tabla 'solicitudes_presupuesto'
        # Asegúrate de que la tabla ya existe en tu base de datos PostgreSQL local
        cur.execute(
            """
            INSERT INTO solicitudes_presupuesto (nombre, correo, whatsapp, descripcion)
            VALUES (%s, %s, %s, %s) RETURNING id;
            """,
            (nombre, correo, whatsapp, descripcion)
        )
        new_id = cur.fetchone()[0] # Obtiene el ID de la fila insertada
        conn.commit() # Confirma los cambios en la base de datos
        cur.close()

        print(f"Datos insertados en la base de datos local con ID: {new_id}")
        return jsonify({"message": "¡Tu solicitud ha sido enviada con éxito!", "data": {"id": new_id}}), 200

    except Exception as e:
        print(f"Error al insertar en la base de datos local: {e}")
        if conn:
            conn.rollback() # Revierte los cambios si hay un error
        return jsonify({"message": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        if conn:
            conn.close() # Asegura que la conexión se cierre

# Punto de entrada para ejecutar la aplicación Flask
if __name__ == '__main__':
    # El puerto por defecto para Flask es 5000, pero puedes usar 3000 si lo prefieres
    port = int(os.environ.get("PORT", 3000))
    app.run(debug=True, host='0.0.0.0', port=port)
