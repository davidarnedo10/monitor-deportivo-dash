# gestor_futbol.py - Gestor de jugadores de fútbol
import sqlite3
import datetime
import json
import os

class GestorFutbol:
    def __init__(self, db_path="data/futbol.db"):
        """Inicializa el gestor de futbolistas"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos de jugadores"""
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Tabla de jugadores
        c.execute("""
            CREATE TABLE IF NOT EXISTS jugadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                posicion TEXT NOT NULL,
                numero INTEGER,
                edad INTEGER NOT NULL,
                peso REAL NOT NULL,
                altura INTEGER NOT NULL,
                pie_habil TEXT DEFAULT 'Derecho',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Tabla de métricas deportivas
        c.execute("""
            CREATE TABLE IF NOT EXISTS metricas_deportivas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jugador_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                tipo_metrica TEXT NOT NULL,
                valor REAL NOT NULL,
                unidad TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
            )
        """)
        
        # Tabla de entrenamientos
        c.execute("""
            CREATE TABLE IF NOT EXISTS entrenamientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jugador_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                tipo TEXT DEFAULT 'General',
                duracion REAL,
                intensidad INTEGER,
                notas TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
            )
        """)
        
        # Tabla de lesiones
        c.execute("""
            CREATE TABLE IF NOT EXISTS lesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jugador_id INTEGER NOT NULL,
                fecha_lesion TEXT NOT NULL,
                tipo_lesion TEXT NOT NULL,
                gravedad TEXT,
                dias_recuperacion INTEGER,
                notas TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
            )
        """)
        
        # Índices para mejorar rendimiento
        c.execute("CREATE INDEX IF NOT EXISTS idx_jugadores_user_id ON jugadores(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_metricas_jugador_id ON metricas_deportivas(jugador_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_entrenamientos_jugador_id ON entrenamientos(jugador_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_lesiones_jugador_id ON lesiones(jugador_id)")
        
        conn.commit()
        conn.close()
        print("✅ Base de datos de fútbol inicializada")
    
    def agregar_jugador(self, datos_jugador, user_id=None):
        """Agrega un nuevo jugador"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("""
                INSERT INTO jugadores (
                    nombre, posicion, numero, edad, peso, 
                    altura, pie_habil, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos_jugador.get('nombre', 'Nuevo Jugador'),
                datos_jugador.get('posicion', 'Mediocentro'),
                datos_jugador.get('numero'),
                datos_jugador.get('edad', 25),
                datos_jugador.get('peso', 75.0),
                datos_jugador.get('altura', 180),
                datos_jugador.get('pie_habil', 'Derecho'),
                user_id
            ))
            
            jugador_id = c.lastrowid
            conn.commit()
            
            # Crear métricas iniciales
            self._crear_metricas_iniciales(jugador_id)
            
            return jugador_id
        except Exception as e:
            print(f"❌ Error agregando jugador: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            conn.close()
    
    def _crear_metricas_iniciales(self, jugador_id):
        """Crea métricas iniciales para un nuevo jugador"""
        metricas_iniciales = [
            ('Velocidad Máxima', 30.5, 'km/h'),
            ('Aceleración 0-20m', 3.2, 'seg'),
            ('Fuerza de Salto', 45.2, 'cm'),
            ('VO2 Máximo', 55.3, 'ml/kg/min'),
            ('Fuerza en Piernas', 120.5, 'kg')
        ]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        fecha = datetime.datetime.now().strftime("%Y-%m-%d")
        for tipo, valor, unidad in metricas_iniciales:
            try:
                c.execute("""
                    INSERT INTO metricas_deportivas (jugador_id, fecha, tipo_metrica, valor, unidad)
                    VALUES (?, ?, ?, ?, ?)
                """, (jugador_id, fecha, tipo, valor, unidad))
            except Exception as e:
                print(f"Error creando métrica inicial: {e}")
        
        conn.commit()
        conn.close()
    
    def obtener_jugadores(self, user_id=None):
        """Obtiene todos los jugadores"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if user_id:
            c.execute("""
                SELECT id, nombre, posicion, numero, edad, peso, altura, pie_habil, created_at 
                FROM jugadores 
                WHERE user_id=? 
                ORDER BY created_at DESC
            """, (user_id,))
        else:
            c.execute("""
                SELECT id, nombre, posicion, numero, edad, peso, altura, pie_habil, created_at 
                FROM jugadores 
                ORDER BY created_at DESC
            """)
        
        jugadores = []
        for row in c.fetchall():
            jugadores.append({
                'id': row[0],
                'nombre': row[1],
                'posicion': row[2],
                'numero': row[3],
                'edad': row[4],
                'peso': row[5],
                'altura': row[6],
                'pie_habil': row[7],
                'created_at': row[8]
            })
        
        conn.close()
        return jugadores
    
    def obtener_jugador(self, jugador_id):
        """Obtiene un jugador específico con todas sus métricas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Obtener información básica
        c.execute("""
            SELECT id, nombre, posicion, numero, edad, peso, altura, pie_habil, created_at 
            FROM jugadores 
            WHERE id=?
        """, (jugador_id,))
        
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        
        jugador = {
            'id': row[0],
            'nombre': row[1],
            'posicion': row[2],
            'numero': row[3],
            'edad': row[4],
            'peso': row[5],
            'altura': row[6],
            'pie_habil': row[7],
            'created_at': row[8],
            'info': {
                'nombre': row[1],
                'posicion': row[2],
                'numero': row[3],
                'edad': row[4],
                'peso': row[5],
                'altura': row[6],
                'pie_habil': row[7]
            }
        }
        
        # Obtener métricas
        c.execute("""
            SELECT fecha, tipo_metrica, valor, unidad 
            FROM metricas_deportivas 
            WHERE jugador_id=? 
            ORDER BY fecha DESC 
            LIMIT 20
        """, (jugador_id,))
        
        metricas = []
        for m in c.fetchall():
            metricas.append({
                'fecha': m[0],
                'tipo': m[1],
                'valor': m[2],
                'unidad': m[3]
            })
        
        jugador['metricas'] = metricas
        
        # Obtener entrenamientos recientes
        c.execute("""
            SELECT fecha, tipo, duracion, intensidad, notas 
            FROM entrenamientos 
            WHERE jugador_id=? 
            ORDER BY fecha DESC 
            LIMIT 10
        """, (jugador_id,))
        
        entrenamientos = []
        for e in c.fetchall():
            entrenamientos.append({
                'fecha': e[0],
                'tipo': e[1],
                'duracion': e[2],
                'intensidad': e[3],
                'notas': e[4]
            })
        
        jugador['entrenamientos'] = entrenamientos
        
        # Obtener lesiones
        c.execute("""
            SELECT fecha_lesion, tipo_lesion, gravedad, dias_recuperacion, notas 
            FROM lesiones 
            WHERE jugador_id=? 
            ORDER BY fecha_lesion DESC 
            LIMIT 5
        """, (jugador_id,))
        
        lesiones = []
        for l in c.fetchall():
            lesiones.append({
                'fecha': l[0],
                'tipo': l[1],
                'gravedad': l[2],
                'dias_recuperacion': l[3],
                'notas': l[4]
            })
        
        jugador['lesiones'] = lesiones
        
        conn.close()
        return jugador
    
    def eliminar_jugador(self, jugador_id):
        """Elimina un jugador y todos sus datos asociados"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Eliminar datos relacionados
            c.execute("DELETE FROM metricas_deportivas WHERE jugador_id=?", (jugador_id,))
            c.execute("DELETE FROM entrenamientos WHERE jugador_id=?", (jugador_id,))
            c.execute("DELETE FROM lesiones WHERE jugador_id=?", (jugador_id,))
            
            # Eliminar el jugador
            c.execute("DELETE FROM jugadores WHERE id=?", (jugador_id,))
            
            conn.commit()
            print(f"✅ Jugador {jugador_id} eliminado")
            return True
        except Exception as e:
            print(f"❌ Error eliminando jugador: {e}")
            return False
        finally:
            conn.close()
    
    def agregar_metrica(self, jugador_id, tipo_metrica, valor, unidad="", fecha=None):
        """Agrega una métrica para un jugador"""
        if fecha is None:
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("""
                INSERT INTO metricas_deportivas (jugador_id, fecha, tipo_metrica, valor, unidad)
                VALUES (?, ?, ?, ?, ?)
            """, (jugador_id, fecha, tipo_metrica, valor, unidad))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error agregando métrica: {e}")
            return False
        finally:
            conn.close()
    
    def agregar_entrenamiento(self, jugador_id, fecha, tipo="General", duracion=60, intensidad=5, notas=""):
        """Agrega un registro de entrenamiento"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("""
                INSERT INTO entrenamientos (jugador_id, fecha, tipo, duracion, intensidad, notas)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (jugador_id, fecha, tipo, duracion, intensidad, notas))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error agregando entrenamiento: {e}")
            return False
        finally:
            conn.close()
    
    def agregar_lesion(self, jugador_id, fecha_lesion, tipo_lesion, gravedad="Moderada", dias_recuperacion=14, notas=""):
        """Agrega un registro de lesión"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("""
                INSERT INTO lesiones (jugador_id, fecha_lesion, tipo_lesion, gravedad, dias_recuperacion, notas)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (jugador_id, fecha_lesion, tipo_lesion, gravedad, dias_recuperacion, notas))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error agregando lesión: {e}")
            return False
        finally:
            conn.close()
    
    def obtener_estadisticas_jugador(self, jugador_id):
        """Obtiene estadísticas del jugador"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        estadisticas = {}
        
        # Total de métricas
        c.execute("SELECT COUNT(*) FROM metricas_deportivas WHERE jugador_id=?", (jugador_id,))
        estadisticas['total_metricas'] = c.fetchone()[0] or 0
        
        # Total de entrenamientos
        c.execute("SELECT COUNT(*) FROM entrenamientos WHERE jugador_id=?", (jugador_id,))
        estadisticas['total_entrenamientos'] = c.fetchone()[0] or 0
        
        # Horas totales de entrenamiento
        c.execute("SELECT SUM(duracion) FROM entrenamientos WHERE jugador_id=?", (jugador_id,))
        total_minutos = c.fetchone()[0] or 0
        estadisticas['horas_entrenamiento'] = round(total_minutos / 60, 1)
        
        # Total de lesiones
        c.execute("SELECT COUNT(*) FROM lesiones WHERE jugador_id=?", (jugador_id,))
        estadisticas['total_lesiones'] = c.fetchone()[0] or 0
        
        # Última métrica
        c.execute("""
            SELECT tipo_metrica, valor, unidad, fecha 
            FROM metricas_deportivas 
            WHERE jugador_id=? 
            ORDER BY fecha DESC 
            LIMIT 1
        """, (jugador_id,))
        
        ultima_metrica = c.fetchone()
        if ultima_metrica:
            estadisticas['ultima_metrica'] = {
                'tipo': ultima_metrica[0],
                'valor': ultima_metrica[1],
                'unidad': ultima_metrica[2],
                'fecha': ultima_metrica[3]
            }
        
        conn.close()
        return estadisticas

# Funciones de compatibilidad para código existente
def agregar_jugador(datos):
    """Wrapper para compatibilidad"""
    gestor = GestorFutbol()
    return gestor.agregar_jugador(datos)

def obtener_jugadores():
    """Wrapper para compatibilidad"""
    gestor = GestorFutbol()
    return gestor.obtener_jugadores()

def eliminar_jugador(jugador_id):
    """Wrapper para compatibilidad"""
    gestor = GestorFutbol()
    return gestor.eliminar_jugador(jugador_id)

if __name__ == "__main__":
    gestor = GestorFutbol()
    print("✅ Gestor de fútbol inicializado y listo")