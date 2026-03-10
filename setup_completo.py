import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = "data/gestor_futbol.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    """Configura la base de datos completa"""
    print("=" * 60)
    print("⚙️  CONFIGURANDO BASE DE DATOS")
    print("=" * 60)
    
    # Crear carpeta data
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # ============================================
    # TABLA DE USUARIOS (ENTRENADORES)
    # ============================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nombre TEXT,
        apellidos TEXT,
        email TEXT,
        telefono TEXT,
        equipo TEXT,
        fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
        ultimo_acceso TEXT,
        avatar TEXT
    )
    """)
    print("✅ Tabla 'users' lista")
    
    # ============================================
    # TABLA DE FUTBOLISTAS
    # ============================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS futbolistas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        apellidos TEXT,
        edad INTEGER,
        posicion TEXT,
        dorsal INTEGER,
        pierna_buena TEXT,
        altura REAL,
        peso REAL,
        fecha_nacimiento TEXT,
        nacionalidad TEXT,
        equipo_actual TEXT,
        foto TEXT,
        activo INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    print("✅ Tabla 'futbolistas' lista")
    
    # ============================================
    # TABLA DE SESIONES (DATOS DE SENSORES)
    # ============================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        futbolista_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('entrenamiento', 'partido', 'recuperacion')),
        titulo TEXT,
        duracion INTEGER,
        distancia_total REAL,
        velocidad_maxima REAL,
        velocidad_media REAL,
        sprints INTEGER,
        impactos INTEGER,
        frecuencia_cardiaca_media INTEGER,
        frecuencia_cardiaca_max INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(futbolista_id) REFERENCES futbolistas(id)
    )
    """)
    print("✅ Tabla 'sesiones' lista")
    
    # ============================================
    # TABLA DE PARTIDOS
    # ============================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        futbolista_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        rival TEXT,
        competicion TEXT,
        local INTEGER DEFAULT 1,
        resultado TEXT,
        minutos_jugados INTEGER,
        goles INTEGER DEFAULT 0,
        asistencias INTEGER DEFAULT 0,
        tiros INTEGER DEFAULT 0,
        pases_completados INTEGER DEFAULT 0,
        pases_totales INTEGER DEFAULT 0,
        faltas INTEGER DEFAULT 0,
        tarjetas_amarillas INTEGER DEFAULT 0,
        tarjetas_rojas INTEGER DEFAULT 0,
        valoracion REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(futbolista_id) REFERENCES futbolistas(id)
    )
    """)
    print("✅ Tabla 'partidos' lista")
    
    # ============================================
    # TABLA DE CUESTIONARIOS
    # ============================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS cuestionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        futbolista_id INTEGER NOT NULL,
        fecha TEXT DEFAULT CURRENT_TIMESTAMP,
        fatiga INTEGER CHECK(fatiga BETWEEN 1 AND 10),
        sueno_calidad INTEGER CHECK(sueno_calidad BETWEEN 1 AND 10),
        sueno_horas REAL,
        dolor_muscular INTEGER CHECK(dolor_muscular BETWEEN 1 AND 10),
        estres INTEGER CHECK(estres BETWEEN 1 AND 10),
        motivacion INTEGER CHECK(motivacion BETWEEN 1 AND 10),
        rpe INTEGER CHECK(rpe BETWEEN 1 AND 10),
        observaciones TEXT,
        FOREIGN KEY(futbolista_id) REFERENCES futbolistas(id)
    )
    """)
    print("✅ Tabla 'cuestionarios' lista")
    
    # ============================================
    # ÍNDICES PARA MEJORAR RENDIMIENTO
    # ============================================
    c.execute("CREATE INDEX IF NOT EXISTS idx_futbolistas_user ON futbolistas(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_futbolista ON sesiones(futbolista_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_partidos_futbolista ON partidos(futbolista_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cuestionarios_futbolista ON cuestionarios(futbolista_id)")
    print("✅ Índices creados")
    
    conn.commit()
    conn.close()
    print("=" * 60)
    print("✅ BASE DE DATOS CONFIGURADA CORRECTAMENTE")
    print("=" * 60)

def crear_usuario_entrenador(username, password, nombre, email, equipo):
    """Crea un nuevo entrenador"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    hashed = hash_password(password)
    try:
        c.execute("""
            INSERT INTO users (username, password, nombre, email, equipo, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, hashed, nombre, email, equipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        user_id = c.lastrowid
        print(f"✅ Entrenador '{username}' creado con ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError:
        print(f"❌ El usuario '{username}' ya existe")
        return None
    finally:
        conn.close()

def añadir_jugadores_prueba(user_id):
    """Añade jugadores de prueba para un entrenador"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    jugadores = [
        ("Lionel", "Messi", 36, "Delantero", 10, "Derecha", 170, 72, "1987-06-24", "Argentina"),
        ("Cristiano", "Ronaldo", 39, "Delantero", 7, "Derecha", 187, 85, "1985-02-05", "Portugal"),
        ("Kylian", "Mbappé", 25, "Delantero", 9, "Derecha", 178, 73, "1998-12-20", "Francia"),
        ("Luka", "Modric", 38, "Centrocampista", 10, "Derecha", 172, 66, "1985-09-09", "Croacia"),
        ("Sergio", "Ramos", 37, "Defensa", 4, "Derecha", 184, 82, "1986-03-30", "España"),
    ]
    
    for nombre, apellidos, edad, posicion, dorsal, pierna, altura, peso, fecha_nac, nacionalidad in jugadores:
        try:
            c.execute("""
                INSERT INTO futbolistas 
                (user_id, nombre, apellidos, edad, posicion, dorsal, pierna_buena, altura, peso, fecha_nacimiento, nacionalidad)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, nombre, apellidos, edad, posicion, dorsal, pierna, altura, peso, fecha_nac, nacionalidad))
            print(f"  ✅ {nombre} {apellidos} añadido")
        except Exception as e:
            print(f"  ❌ Error añadiendo {nombre}: {e}")
    
    conn.commit()
    conn.close()

def verificar_datos():
    """Verifica que todo esté correcto"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📊 VERIFICANDO DATOS")
    print("=" * 60)
    
    # Ver entrenadores
    c.execute("SELECT id, username, nombre, equipo FROM users")
    entrenadores = c.fetchall()
    print(f"\n👤 ENTRENADORES ({len(entrenadores)}):")
    for e in entrenadores:
        print(f"  ID: {e[0]} | {e[1]} | {e[2]} | Equipo: {e[3]}")
        
        # Ver jugadores de este entrenador
        c.execute("SELECT COUNT(*) FROM futbolistas WHERE user_id=?", (e[0],))
        total = c.fetchone()[0]
        print(f"    ⚽ Jugadores: {total}")
        
        if total > 0:
            c.execute("SELECT id, nombre, apellidos, posicion, dorsal FROM futbolistas WHERE user_id=? LIMIT 3", (e[0],))
            for j in c.fetchall():
                print(f"      - {j[1]} {j[2]} | {j[3]} #{j[4]}")
    
    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    # 1. Configurar base de datos
    setup_database()
    
    # 2. Crear entrenadores de prueba
    print("\n" + "=" * 60)
    print("👤 CREANDO ENTRENADORES")
    print("=" * 60)
    
    # Entrenador 1: admin
    admin_id = crear_usuario_entrenador("admin", "admin123", "Administrador", "admin@futbol.com", "Selección Nacional")
    
    # Entrenador 2: carlos
    carlos_id = crear_usuario_entrenador("carlos", "carlos123", "Carlos Martínez", "carlos@futbol.com", "Real Madrid FC")
    
    # Entrenador 3: pedro
    pedro_id = crear_usuario_entrenador("pedro", "pedro123", "Pedro Sánchez", "pedro@futbol.com", "FC Barcelona")
    
    # 3. Añadir jugadores a cada entrenador
    if admin_id:
        print("\n⚽ AÑADIENDO JUGADORES A ADMIN:")
        añadir_jugadores_prueba(admin_id)
    
    if carlos_id:
        print("\n⚽ AÑADIENDO JUGADORES A CARLOS:")
        jugadores_carlos = [
            ("Vinícius", "Júnior", 23, "Delantero", 7, "Derecha", 176, 73, "2000-07-12", "Brasil"),
            ("Jude", "Bellingham", 20, "Centrocampista", 5, "Derecha", 186, 75, "2003-06-29", "Inglaterra"),
            ("Rodrygo", "Goes", 22, "Delantero", 11, "Derecha", 174, 64, "2001-01-09", "Brasil"),
        ]
        for j in jugadores_carlos:
            try:
                c = conn = sqlite3.connect(DB_PATH)
                c.execute("""
                    INSERT INTO futbolistas (user_id, nombre, apellidos, edad, posicion, dorsal, pierna_buena, altura, peso, fecha_nacimiento, nacionalidad)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (carlos_id, j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]))
                c.commit()
                c.close()
                print(f"  ✅ {j[0]} {j[1]} añadido")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    if pedro_id:
        print("\n⚽ AÑADIENDO JUGADORES A PEDRO:")
        jugadores_pedro = [
            ("Robert", "Lewandowski", 35, "Delantero", 9, "Derecha", 185, 81, "1988-08-21", "Polonia"),
            ("Pedri", "González", 21, "Centrocampista", 8, "Derecha", 174, 64, "2002-11-25", "España"),
            ("Gavi", "Páez", 19, "Centrocampista", 6, "Derecha", 173, 70, "2004-08-05", "España"),
        ]
        for j in jugadores_pedro:
            try:
                c = conn = sqlite3.connect(DB_PATH)
                c.execute("""
                    INSERT INTO futbolistas (user_id, nombre, apellidos, edad, posicion, dorsal, pierna_buena, altura, peso, fecha_nacimiento, nacionalidad)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pedro_id, j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]))
                c.commit()
                c.close()
                print(f"  ✅ {j[0]} {j[1]} añadido")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    # 4. Verificar todo
    verificar_datos()
    
    print("\n" + "=" * 60)
    print("🚀 LISTO! Usuarios creados:")
    print("  admin / admin123 - Selección Nacional")
    print("  carlos / carlos123 - Real Madrid FC")
    print("  pedro / pedro123 - FC Barcelona")
    print("=" * 60)