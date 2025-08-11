import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Para manejar CORS
import psycopg2 # Importamos la librería para PostgreSQL
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

# Configuración de las credenciales de la base de datos PostgreSQL en Render
# Render proporciona una única DATABASE_URL que incluye todos los detalles.
# Alternativamente, podrías configurar DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT.
# La URL externa proporcionada por el usuario es: postgresql://costura_latina_bd_user:JVdZaC87KNa5UtIzXQ4kQUmE89a5Jtzf@dpg-d2ctvaadbo4c73c4g3lg-a.singapore-postgres.render.com/costura_latina_bd
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://costura_latina_bd_user:JVdZaC87KNa5UtIzXQ4kQUmE89a5Jtzf@dpg-d2ctvaadbo4c73c4g3lg-a.singapore-postgres.render.com/costura_latina_bd")


# Verifica que la URL de la base de datos esté configurada
if not DATABASE_URL:
    print("Error: La variable de entorno DATABASE_URL no está configurada.")
    exit(1) # Sale de la aplicación si faltan las credenciales

# Función para establecer la conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require') # 'sslmode=require' es importante para Render
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

print(f"La aplicación Flask está lista para conectarse a la base de datos.")

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
        # Asegúrate de que la tabla ya existe en tu base de datos de Render
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

        print(f"Datos insertados en la base de datos de Render con ID: {new_id}")
        return jsonify({"message": "¡Tu solicitud ha sido enviada con éxito!", "data": {"id": new_id}}), 200

    except Exception as e:
        print(f"Error al insertar en la base de datos: {e}")
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
