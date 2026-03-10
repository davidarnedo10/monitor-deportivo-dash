import sqlite3
import datetime
import os

# Ruta de la base de datos (archivo dentro de la carpeta data)
DB_PATH = "data/users.db"

def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabla de usuarios (entrenadores)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabla de pacientes asociados a entrenadores
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        edad INTEGER,
        peso REAL,
        altura REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # Tabla de cuestionarios (registros diarios)
    c.execute("""
    CREATE TABLE IF NOT EXISTS questionnaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        fatiga INTEGER CHECK(fatiga >= 1 AND fatiga <= 10),
        suenio INTEGER CHECK(suenio >= 1 AND suenio <= 10),
        rpe INTEGER CHECK(rpe >= 1 AND rpe <= 10),
        tiempo_entrenamiento REAL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    )
    """)

    # Tabla de entrenamientos (sesiones completas)
    c.execute("""
    CREATE TABLE IF NOT EXISTS entrenamientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        tipo TEXT DEFAULT 'General',
        duracion REAL,
        notas TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    )
    """)

    # Tabla de métricas deportivas (para futuras expansiones)
    c.execute("""
    CREATE TABLE IF NOT EXISTS metricas_deportivas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        tipo_metrica TEXT NOT NULL,
        valor REAL NOT NULL,
        unidad TEXT,
        fecha TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    )
    """)

    # Índices para mejorar el rendimiento
    c.execute("CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_questionnaires_patient_id ON questionnaires(patient_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_questionnaires_timestamp ON questionnaires(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_entrenamientos_patient_id ON entrenamientos(patient_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_entrenamientos_fecha ON entrenamientos(fecha)")

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

# ---------- USUARIOS ----------
def add_user(username, password):
    """Añade un nuevo usuario (entrenador) a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def user_exists(username):
    """Verifica si un usuario existe"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username=?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def authenticate_user(username, password):
    """Autentica un usuario con nombre de usuario y contraseña"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_id(username):
    """Obtiene el ID de usuario por nombre de usuario"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_user_stats(username):
    """Obtiene estadísticas del usuario"""
    user_id = get_user_id(username)
    if user_id is None:
        return None
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Contar pacientes
    c.execute("SELECT COUNT(*) FROM patients WHERE user_id=?", (user_id,))
    total_pacientes = c.fetchone()[0]
    
    # Obtener último paciente creado
    c.execute("SELECT id, full_name FROM patients WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,))
    ultimo_paciente = c.fetchone()
    
    # Obtener total de cuestionarios
    c.execute("""
        SELECT COUNT(*) FROM questionnaires q
        JOIN patients p ON q.patient_id = p.id 
        WHERE p.user_id=?
    """, (user_id,))
    total_cuestionarios = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total_pacientes": total_pacientes,
        "ultimo_paciente": ultimo_paciente,
        "total_cuestionarios": total_cuestionarios
    }

# ---------- PACIENTES ----------
def get_patients_by_user(username):
    """
    Devuelve lista de pacientes del usuario con información básica
    """
    user_id = get_user_id(username)
    if user_id is None:
        return []

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, full_name, edad, peso, altura, created_at 
        FROM patients 
        WHERE user_id=? 
        ORDER BY created_at DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()

    patients = []
    for row in rows:
        pid, full_name, edad, peso, altura, created_at = row
        patients.append({
            "id": pid,
            "name": full_name or f"Deportista {pid}",
            "full_name": full_name,
            "edad": edad,
            "peso": peso,
            "altura": altura,
            "created_at": created_at
        })
    return patients

def create_patient(username):
    """
    Crea un paciente asociado al usuario
    Devuelve el nuevo patient_id (int) o None en caso de error
    """
    user_id = get_user_id(username)
    if user_id is None:
        return None

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Contar pacientes existentes del usuario para nombrado por defecto
    c.execute("SELECT COUNT(*) FROM patients WHERE user_id = ?", (user_id,))
    count = c.fetchone()[0] or 0
    new_name = f"Deportista {count + 1}"

    # Insertar nuevo paciente
    c.execute(
        "INSERT INTO patients (user_id, full_name, edad, peso, altura) VALUES (?, ?, ?, ?, ?)",
        (user_id, new_name, None, None, None)
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def get_last_patient_for_user(username):
    """Obtiene el último paciente creado por el usuario"""
    user_id = get_user_id(username)
    if user_id is None:
        return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM patients WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_patient_info(patient_id):
    """
    Devuelve información completa del paciente
    """
    if not patient_id:
        return {"full_name": "", "edad": "", "peso": "", "altura": ""}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT full_name, edad, peso, altura, created_at 
        FROM patients WHERE id=?
    """, (patient_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"full_name": "", "edad": "", "peso": "", "altura": ""}
    
    return {
        "full_name": row[0] or "", 
        "edad": row[1] if row[1] is not None else "", 
        "peso": row[2] if row[2] is not None else "", 
        "altura": row[3] if row[3] is not None else "",
        "created_at": row[4]
    }

def save_patient_info(patient_id, full_name, edad, peso, altura):
    """Guarda/actualiza la información del paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE patients 
        SET full_name=?, edad=?, peso=?, altura=?, created_at=CURRENT_TIMESTAMP 
        WHERE id=?
    """, (full_name, edad, peso, altura, patient_id))
    conn.commit()
    conn.close()

def delete_patient(patient_id):
    """Elimina un paciente y todos sus datos asociados"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Primero eliminar datos relacionados
        c.execute("DELETE FROM questionnaires WHERE patient_id=?", (patient_id,))
        c.execute("DELETE FROM entrenamientos WHERE patient_id=?", (patient_id,))
        c.execute("DELETE FROM metricas_deportivas WHERE patient_id=?", (patient_id,))
        # Luego eliminar el paciente
        c.execute("DELETE FROM patients WHERE id=?", (patient_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error eliminando paciente: {e}")
        return False
    finally:
        conn.close()

def get_patient_stats(patient_id):
    """Obtiene estadísticas del paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total de cuestionarios
    c.execute("SELECT COUNT(*) FROM questionnaires WHERE patient_id=?", (patient_id,))
    total_cuestionarios = c.fetchone()[0]
    
    # Último cuestionario
    c.execute("""
        SELECT timestamp, fatiga, suenio, rpe, tiempo_entrenamiento
        FROM questionnaires 
        WHERE patient_id=? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (patient_id,))
    ultimo_cuestionario = c.fetchone()
    
    # Promedio de fatiga
    c.execute("SELECT AVG(fatiga) FROM questionnaires WHERE patient_id=?", (patient_id,))
    avg_fatiga = c.fetchone()[0]
    
    # Promedio de sueño
    c.execute("SELECT AVG(suenio) FROM questionnaires WHERE patient_id=?", (patient_id,))
    avg_suenio = c.fetchone()[0]
    
    # Total de entrenamientos
    c.execute("SELECT COUNT(*) FROM entrenamientos WHERE patient_id=?", (patient_id,))
    total_entrenamientos = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total_cuestionarios": total_cuestionarios,
        "ultimo_cuestionario": ultimo_cuestionario,
        "avg_fatiga": round(avg_fatiga, 1) if avg_fatiga else 0,
        "avg_suenio": round(avg_suenio, 1) if avg_suenio else 0,
        "total_entrenamientos": total_entrenamientos
    }

# ---------- CUESTIONARIOS ----------
def save_questionnaire_for_patient(patient_id, fatiga, suenio, rpe, tiempo_entrenamiento):
    """Guarda un cuestionario diario para un paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO questionnaires (patient_id, fatiga, suenio, rpe, tiempo_entrenamiento)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, fatiga, suenio, rpe, tiempo_entrenamiento))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error guardando cuestionario: {e}")
        return False
    finally:
        conn.close()

def get_questionnaires_for_patient(patient_id, limit=10):
    """Obtiene los últimos cuestionarios de un paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, fatiga, suenio, rpe, tiempo_entrenamiento
        FROM questionnaires 
        WHERE patient_id=?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (patient_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_training_data_for_patient(patient_id):
    """Obtiene datos de entrenamiento para gráficos"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, (rpe * tiempo_entrenamiento) AS carga
        FROM questionnaires 
        WHERE patient_id=?
        ORDER BY timestamp ASC
    """, (patient_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_questionnaire_stats(patient_id, days=7):
    """Obtiene estadísticas de cuestionarios recientes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            AVG(fatiga) as avg_fatiga,
            AVG(suenio) as avg_suenio,
            AVG(rpe) as avg_rpe,
            AVG(tiempo_entrenamiento) as avg_tiempo,
            COUNT(*) as total_registros
        FROM questionnaires 
        WHERE patient_id=? AND timestamp >= date('now', ?)
    """, (patient_id, f'-{days} days'))
    
    stats = c.fetchone()
    conn.close()
    
    if stats and stats[4] > 0:
        return {
            "avg_fatiga": round(stats[0], 1),
            "avg_suenio": round(stats[1], 1),
            "avg_rpe": round(stats[2], 1),
            "avg_tiempo": round(stats[3], 1),
            "total_registros": stats[4]
        }
    return None

# ---------- ENTRENAMIENTOS ----------
def guardar_entrenamiento(patient_id, fecha, tipo, duracion, notas):
    """Guarda un entrenamiento asociado a un paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO entrenamientos (patient_id, fecha, tipo, duracion, notas)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, fecha, tipo, duracion, notas))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error guardando entrenamiento: {e}")
        return False
    finally:
        conn.close()

def obtener_entrenamientos(patient_id, limit=20):
    """Obtiene todos los entrenamientos de un paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT fecha, tipo, duracion, notas, created_at
        FROM entrenamientos
        WHERE patient_id = ?
        ORDER BY fecha DESC
        LIMIT ?
    """, (patient_id, limit))
    entrenamientos = c.fetchall()
    conn.close()
    return entrenamientos

def obtener_estadisticas_entrenamiento(patient_id):
    """Obtiene estadísticas de entrenamiento del paciente"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total de horas entrenadas
    c.execute("SELECT SUM(duracion) FROM entrenamientos WHERE patient_id=?", (patient_id,))
    total_horas = c.fetchone()[0] or 0
    
    # Promedio de duración
    c.execute("SELECT AVG(duracion) FROM entrenamientos WHERE patient_id=?", (patient_id,))
    avg_duracion = c.fetchone()[0] or 0
    
    # Tipo de entrenamiento más común
    c.execute("""
        SELECT tipo, COUNT(*) as count 
        FROM entrenamientos 
        WHERE patient_id=? 
        GROUP BY tipo 
        ORDER BY count DESC 
        LIMIT 1
    """, (patient_id,))
    tipo_comun = c.fetchone()
    
    conn.close()
    
    return {
        "total_horas": round(total_horas / 60, 1),  # Convertir a horas
        "avg_duracion": round(avg_duracion, 1),
        "tipo_comun": tipo_comun[0] if tipo_comun else "No disponible",
        "count_tipo_comun": tipo_comun[1] if tipo_comun else 0
    }

# ---------- FUNCIONES DE MANTENIMIENTO ----------
def actualizar_bd():
    """Actualiza la base de datos manteniendo la compatibilidad"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Verificar si existe la tabla entrenamientos y crear si no existe
        c.execute("""
            CREATE TABLE IF NOT EXISTS entrenamientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                tipo TEXT DEFAULT 'General',
                duracion REAL,
                notas TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            )
        """)
        
        # Verificar columna 'tipo' en entrenamientos
        c.execute("PRAGMA table_info(entrenamientos)")
        columnas_entrenamientos = [col[1] for col in c.fetchall()]
        
        if "tipo" not in columnas_entrenamientos:
            print("🔄 Añadiendo columna 'tipo' a la tabla entrenamientos...")
            c.execute("ALTER TABLE entrenamientos ADD COLUMN tipo TEXT DEFAULT 'General'")
        
        # Verificar columna 'created_at' en las tablas
        for tabla in ['users', 'patients', 'entrenamientos']:
            c.execute(f"PRAGMA table_info({tabla})")
            columnas_tabla = [col[1] for col in c.fetchall()]
            if "created_at" not in columnas_tabla:
                print(f"🔄 Añadiendo columna 'created_at' a la tabla {tabla}...")
                c.execute(f"ALTER TABLE {tabla} ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
        
        # Crear índices si no existen
        c.execute("CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_questionnaires_patient_id ON questionnaires(patient_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_questionnaires_timestamp ON questionnaires(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_entrenamientos_patient_id ON entrenamientos(patient_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_entrenamientos_fecha ON entrenamientos(fecha)")
        
        conn.commit()
        print("✅ Base de datos actualizada correctamente")
        
    except Exception as e:
        print(f"❌ Error actualizando base de datos: {e}")
    finally:
        conn.close()

def backup_database():
    """Crea una copia de seguridad de la base de datos"""
    import shutil
    import datetime
    
    if not os.path.exists(DB_PATH):
        return False
        
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"users_backup_{timestamp}.db")
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Copia de seguridad creada: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error creando copia de seguridad: {e}")
        return False

# ---------- WRAPPERS PARA COMPATIBILIDAD ----------
def save_questionnaire(patient_id, fatiga, suenio, rpe, tiempo_entrenamiento):
    """Wrapper para mantener compatibilidad con código existente"""
    return save_questionnaire_for_patient(patient_id, fatiga, suenio, rpe, tiempo_entrenamiento)

def get_training_data(patient_id):
    """Wrapper para mantener compatibilidad con código existente"""
    return get_training_data_for_patient(patient_id)

# Función de compatibilidad para código existente que usa 'paciente_id'
def guardar_entrenamiento_compat(paciente_id, fecha, tipo, duracion, notas):
    """Wrapper para compatibilidad con código que usa 'paciente_id'"""
    return guardar_entrenamiento(paciente_id, fecha, tipo, duracion, notas)

def obtener_entrenamientos_compat(paciente_id):
    """Wrapper para compatibilidad con código que usa 'paciente_id'"""
    return obtener_entrenamientos(paciente_id)

# ---------- INICIALIZACIÓN ----------
if __name__ == "__main__":
    init_db()
    actualizar_bd()
    print("🏁 Base de datos lista para usar")