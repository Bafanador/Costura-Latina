import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Para manejar CORS
import psycopg2 # Cliente de PostgreSQL para Python
from dotenv import load_dotenv # Para cargar variables de entorno (para desarrollo local)

# Carga las variables de entorno del archivo .env si ejecutas localmente.
# En Render, configurarás estas variables directamente en la plataforma.
load_dotenv()

# Inicializa la aplicación Flask
app = Flask(__name__)
# Configura CORS. En desarrollo, permitimos todos los orígenes.
# En producción, deberías restringir 'origins' a la URL específica de tu frontend.
CORS(app, origins="*", methods=["GET", "POST"], allow_headers=["Content-Type"])

# Configuración de la URL de conexión a la base de datos CockroachDB Serverless
# Render y CockroachDB Cloud suelen proporcionar una DATABASE_URL completa.
# Esta URL se obtendrá de las variables de entorno de Render.
DATABASE_URL = os.environ.get("DATABASE_URL")

# Verifica que la URL de la base de datos esté configurada
if not DATABASE_URL:
    print("Error: La variable de entorno DATABASE_URL no está configurada.")
    exit(1) # Sale de la aplicación si faltan las credenciales

# Función para establecer la conexión a la base de datos
def get_db_connection():
    try:
        # psycopg2 puede conectar usando la cadena de conexión completa.
        # Aquí, pasamos sslmode='require' explícitamente para anular cualquier sslmode
        # en la URL y evitar el error de certificado en Render.
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Por seguridad y para consistencia en la codificación.
        conn.set_session(autocommit=True)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos CockroachDB: {e}")
        return None

print(f"La aplicación Flask está lista para conectarse a CockroachDB Serverless.")

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
            return jsonify({"message": "Error interno del servidor: Fallo en la conexión a la base de datos."}), 500

        cur = conn.cursor()

        # Inserta los datos en la tabla 'solicitudes_presupuesto'
        # Usamos RETURNING id para obtener el UUID generado por CockroachDB
        cur.execute(
            """
            INSERT INTO solicitudes_presupuesto (nombre, correo, whatsapp, descripcion)
            VALUES (%s, %s, %s, %s) RETURNING id;
            """,
            (nombre, correo, whatsapp, descripcion)
        )
        new_id = cur.fetchone()[0] # Obtiene el UUID de la fila insertada
        conn.commit() # Confirma los cambios en la base de datos
        cur.close()

        print(f"Datos insertados en CockroachDB con ID: {new_id}")
        return jsonify({"message": "¡Tu solicitud ha sido enviada con éxito!", "data": {"id": str(new_id)}}), 200

    except Exception as e:
        print(f"Error al insertar en CockroachDB: {e}")
        if conn:
            conn.rollback() # Revierte los cambios si hay un error
        return jsonify({"message": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        if conn:
            conn.close() # Asegura que la conexión se cierre

# Punto de entrada para ejecutar la aplicación Flask
if __name__ == '__main__':
    # El puerto es manejado por Render automáticamente, pero localmente puedes usar 3000
    port = int(os.environ.get("PORT", 3000))
    app.run(debug=True, host='0.0.0.0', port=port)

