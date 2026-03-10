# app.py - Sistema Completo para Equipos de Fútbol (CON SIMULADOR DE SENSORES) - CORREGIDO
import dash
from dash import html, dcc, Input, Output, State, callback_context
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import json
import os
import hashlib
from collections import Counter
import time
import random

# ============================================
# SISTEMA DE AUTENTICACIÓN PARA ENTRENADORES
# ============================================
class AuthSystem:
    def __init__(self):
        self.users_file = 'deportistas.json'
        self.load_users()
    
    def load_users(self):
        """Cargar usuarios desde archivo JSON"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extraer usuarios de la estructura del archivo
                    if 'usuarios' in data:
                        self.users = data['usuarios']
                    else:
                        self.users = data
            else:
                # Usuarios por defecto para fútbol
                self.users = {
                    'entrenador': {
                        'password': self.hash_password('entrenador123'),
                        'nombre': 'Director Técnico',
                        'email': 'entrenador@club.com',
                        'rol': 'entrenador',
                        'club': 'Club de Fútbol',
                        'fecha_registro': datetime.now().strftime('%Y-%m-%d')
                    },
                    'preparador': {
                        'password': self.hash_password('preparador123'),
                        'nombre': 'Preparador Físico',
                        'email': 'preparador@club.com',
                        'rol': 'preparador',
                        'club': 'Club de Fútbol',
                        'fecha_registro': datetime.now().strftime('%Y-%m-%d')
                    }
                }
                self.save_users()
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
            self.users = {}
    
    def save_users(self):
        """Guardar usuarios en archivo JSON"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando usuarios: {e}")
    
    def hash_password(self, password):
        """Hashear contraseña de forma segura"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, nombre, email, club, rol='entrenador'):
        """Registrar nuevo usuario para el club"""
        if username in self.users:
            return False, "El usuario ya existe"
        
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        
        self.users[username] = {
            'password': self.hash_password(password),
            'nombre': nombre,
            'email': email,
            'rol': rol,
            'club': club,
            'fecha_registro': datetime.now().strftime('%Y-%m-%d')
        }
        self.save_users()
        return True, "Usuario registrado exitosamente"
    
    def verify_login(self, username, password):
        """Verificar credenciales de login"""
        if username in self.users:
            if self.users[username]['password'] == self.hash_password(password):
                return True, self.users[username]
        return False, None

# ============================================
# SISTEMA DE SIMULACIÓN DE SENSORES
# ============================================
class SensorSimulador:
    def __init__(self, gestor_futbol):
        self.gestor = gestor_futbol
        self.datos_sensores = {}
        self.simulando = False
        
    def iniciar_simulacion(self, jugador_id, duracion_minutos=90):
        """Iniciar simulación en tiempo real para un jugador"""
        if jugador_id not in self.gestor.jugadores:
            return False
        
        # Detener simulación anterior si existe
        self.detener_simulacion(jugador_id)
        
        self.datos_sensores[jugador_id] = {
            'activo': True,
            'timestamp_inicio': datetime.now(),
            'duracion': duracion_minutos,
            'datos': [],
            'metricas_acumuladas': {
                'distancia_total': 0,
                'sprints': 0,
                'aceleraciones': 0,
                'contactos_balon': 0,
                'recuperaciones': 0,
                'fatiga_acumulada': 0
            }
        }
        
        # Iniciar simulación en segundo plano
        self.simulando = True
        return True
        
    def _parametros_portero(self):
        return {
            'velocidad_promedio': 2.0,
            'max_sprint': 6.0,
            'prob_contacto_balon': 0.3,
            'zona_actividad': {'x_min': 0, 'x_max': 20, 'y_min': 30, 'y_max': 70},
            'aceleracion_max': 3.0
        }
    
    def _parametros_defensa(self):
        return {
            'velocidad_promedio': 5.5,
            'max_sprint': 8.0,
            'prob_contacto_balon': 0.4,
            'zona_actividad': {'x_min': 0, 'x_max': 60, 'y_min': 10, 'y_max': 90},
            'aceleracion_max': 4.0
        }
    
    def _parametros_mediocampista(self):
        return {
            'velocidad_promedio': 6.5,
            'max_sprint': 9.0,
            'prob_contacto_balon': 0.7,
            'zona_actividad': {'x_min': 20, 'x_max': 80, 'y_min': 20, 'y_max': 80},
            'aceleracion_max': 4.5
        }
    
    def _parametros_delantero(self):
        return {
            'velocidad_promedio': 6.0,
            'max_sprint': 9.5,
            'prob_contacto_balon': 0.5,
            'zona_actividad': {'x_min': 60, 'x_max': 100, 'y_min': 20, 'y_max': 80},
            'aceleracion_max': 5.0
        }
    
    def _generar_datos_segundo(self, posicion, minuto, params):
        """Generar datos para un segundo específico del partido"""
        
        # Patrones de actividad según minuto del partido
        fatiga_factor = 1.0 + (minuto / 90) * 0.5  # Aumenta fatiga progresivamente
        
        # Determinar si está en actividad intensa
        if random.random() < 0.7:  # 70% del tiempo activo
            # Velocidad basada en distribución normal
            velocidad = abs(np.random.normal(
                params['velocidad_promedio'] * (0.9 / fatiga_factor),
                params['velocidad_promedio'] * 0.3
            ))
            
            # ¿Sprint?
            es_sprint = velocidad > params['velocidad_promedio'] * 1.5
            sprint_intensidad = 1 if es_sprint else 0
            
            # Aceleración (m/s²)
            aceleracion = np.random.uniform(0, params['aceleracion_max'])
            
            # Distancia recorrida en este segundo (metros)
            distancia = velocidad * (1000 / 3600)  # Convertir km/h a m/s
            
            # Contacto con balón
            contacto_balon = 1 if random.random() < params['prob_contacto_balon'] / 10 else 0
            
            # Recuperaciones (intercepciones, tackles)
            recuperacion = 1 if random.random() < 0.05 else 0
            
            # Frecuencia cardíaca (latidos por minuto)
            if es_sprint:
                frecuencia = np.random.randint(160, 195)
            else:
                frecuencia = np.random.randint(120, 160)
            
            # Fatiga percibida (escala 1-10)
            fatiga = min(10, 3 + (minuto / 90) * 7 + random.uniform(-1, 1))
            
            # Zona del campo (coordenadas)
            x = np.random.uniform(params['zona_actividad']['x_min'], 
                                 params['zona_actividad']['x_max'])
            y = np.random.uniform(params['zona_actividad']['y_min'], 
                                 params['zona_actividad']['y_max'])
        else:
            # Tiempo de baja actividad (caminando, parado)
            velocidad = np.random.uniform(0, 2.0)
            distancia = velocidad * (1000 / 3600)
            sprint_intensidad = 0
            aceleracion = 0
            contacto_balon = 0
            recuperacion = 0
            frecuencia = np.random.randint(90, 120)
            fatiga = 2 + (minuto / 90) * 3
            x = np.random.uniform(40, 60)  # Zona más central
            y = np.random.uniform(40, 60)
        
        return {
            'velocidad': round(velocidad, 2),
            'distancia': round(distancia, 2),
            'sprint': sprint_intensidad,
            'aceleracion': round(aceleracion, 2),
            'contacto_balon': contacto_balon,
            'recuperacion': recuperacion,
            'frecuencia_cardiaca': frecuencia,
            'fatiga': round(fatiga, 1),
            'posicion_x': round(x, 1),
            'posicion_y': round(y, 1),
            'minuto': round(minuto, 1)
        }
    
    def obtener_datos_tiempo_real(self, jugador_id, ultimos_segundos=30):
        """Obtener datos de los últimos N segundos"""
        if jugador_id not in self.datos_sensores:
            return None
        
        datos = self.datos_sensores[jugador_id]
        if not datos['datos'] or not datos['activo']:
            return None
        
        # Generar datos simulados para el tiempo actual
        if not datos['datos'] or (datetime.now() - datetime.fromisoformat(datos['datos'][-1]['timestamp'])).seconds > 1:
            posicion = self.gestor.jugadores[jugador_id]['posicion']
            if 'Portero' in posicion:
                params = self._parametros_portero()
            elif 'Defensa' in posicion:
                params = self._parametros_defensa()
            elif 'Medio' in posicion:
                params = self._parametros_mediocampista()
            else:
                params = self._parametros_delantero()
            
            minuto_actual = len(datos['datos']) / 60  # Simular progreso del tiempo
            nuevo_dato = self._generar_datos_segundo(posicion, minuto_actual, params)
            nuevo_dato['timestamp'] = datetime.now().isoformat()
            nuevo_dato['minuto'] = minuto_actual
            
            datos['datos'].append(nuevo_dato)
            
            # Actualizar acumulados
            for key in datos['metricas_acumuladas']:
                if key in nuevo_dato:
                    datos['metricas_acumuladas'][key] += nuevo_dato[key]
        
        # Mantener tamaño de datos
        if len(datos['datos']) > 600:
            datos['datos'] = datos['datos'][-600:]
        
        return {
            'datos_recientes': datos['datos'][-ultimos_segundos:] if len(datos['datos']) > ultimos_segundos else datos['datos'],
            'metricas_acumuladas': datos['metricas_acumuladas'],
            'activo': datos['activo'],
            'minuto_actual': datos['datos'][-1]['minuto'] if datos['datos'] else 0
        }
    
    def obtener_estadisticas_partido(self, jugador_id):
        """Obtener estadísticas completas del partido simulado"""
        if jugador_id not in self.datos_sensores:
            return None
        
        datos = self.datos_sensores[jugador_id]
        if not datos['datos']:
            return None
        
        # Calcular métricas
        all_data = datos['datos']
        
        # Velocidades
        velocidades = [d['velocidad'] for d in all_data]
        aceleraciones = [d['aceleracion'] for d in all_data]
        frecuencias = [d['frecuencia_cardiaca'] for d in all_data]
        
        # Zonas de actividad
        posiciones_x = [d['posicion_x'] for d in all_data]
        posiciones_y = [d['posicion_y'] for d in all_data]
        
        return {
            'distancia_total': round(datos['metricas_acumuladas']['distancia_total'] / 1000, 2),  # km
            'sprints_totales': datos['metricas_acumuladas']['sprints'],
            'velocidad_maxima': round(max(velocidades), 1) if velocidades else 0,
            'velocidad_promedio': round(np.mean(velocidades), 1) if velocidades else 0,
            'aceleracion_maxima': round(max(aceleraciones), 1) if aceleraciones else 0,
            'contactos_balon': datos['metricas_acumuladas']['contactos_balon'],
            'recuperaciones': datos['metricas_acumuladas']['recuperaciones'],
            'frecuencia_promedio': round(np.mean(frecuencias)) if frecuencias else 0,
            'frecuencia_maxima': max(frecuencias) if frecuencias else 0,
            'fatiga_final': round(all_data[-1]['fatiga'], 1) if all_data else 0,
            'zona_predominante': self._calcular_zona_predominante(posiciones_x, posiciones_y),
            'intensidad_promedio': round(np.mean([d['sprint'] for d in all_data]) * 100, 1) if all_data else 0
        }
    
    def _calcular_zona_predominante(self, posiciones_x, posiciones_y):
        """Calcular zona del campo donde más tiempo pasa el jugador"""
        if not posiciones_x:
            return "Centro"
        
        x_avg = np.mean(posiciones_x)
        y_avg = np.mean(posiciones_y)
        
        if x_avg < 25:
            zona_x = "Defensiva"
        elif x_avg < 75:
            zona_x = "Centrocampo"
        else:
            zona_x = "Ofensiva"
        
        if y_avg < 33:
            zona_y = "Izquierda"
        elif y_avg < 66:
            zona_y = "Centro"
        else:
            zona_y = "Derecha"
        
        return f"{zona_x} {zona_y}"
    
    def detener_simulacion(self, jugador_id):
        """Detener la simulación para un jugador"""
        if jugador_id in self.datos_sensores:
            self.datos_sensores[jugador_id]['activo'] = False
    
    def guardar_simulacion(self, jugador_id, nombre_partido="Partido de entrenamiento"):
        """Guardar datos de simulación en JSON"""
        if jugador_id not in self.datos_sensores:
            return False
        
        datos = self.datos_sensores[jugador_id]
        estadisticas = self.obtener_estadisticas_partido(jugador_id)
        
        if not estadisticas:
            return False
        
        registro = {
            'jugador_id': jugador_id,
            'nombre_jugador': self.gestor.jugadores[jugador_id]['nombre'],
            'nombre_partido': nombre_partido,
            'fecha': datetime.now().isoformat(),
            'duracion_minutos': datos['duracion'],
            'estadisticas': estadisticas,
            'resumen_datos': {
                'distancia_por_minuto': self._calcular_distancia_por_minuto(datos['datos']),
                'evolucion_fatiga': self._calcular_evolucion_fatiga(datos['datos']),
                'distribucion_zonas': self._calcular_distribucion_zonas(datos['datos'])
            }
        }
        
        # Guardar en archivo
        try:
            archivo = f'simulaciones_{jugador_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(registro, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando simulación: {e}")
            return False
    
    def _calcular_distancia_por_minuto(self, datos):
        """Calcular distancia recorrida por minuto"""
        minutos = {}
        for d in datos:
            minuto = int(d['minuto'])
            if minuto not in minutos:
                minutos[minuto] = 0
            minutos[minuto] += d['distancia']
        
        return {minuto: round(distancia, 2) for minuto, distancia in minutos.items()}
    
    def _calcular_evolucion_fatiga(self, datos):
        """Calcular evolución de la fatiga por minuto"""
        fatiga_por_minuto = {}
        for d in datos:
            minuto = int(d['minuto'])
            if minuto not in fatiga_por_minuto:
                fatiga_por_minuto[minuto] = []
            fatiga_por_minuto[minuto].append(d['fatiga'])
        
        return {minuto: round(np.mean(valores), 1) 
                for minuto, valores in fatiga_por_minuto.items()}
    
    def _calcular_distribucion_zonas(self, datos):
        """Calcular distribución por zonas del campo"""
        zonas = {
            'Defensiva Izquierda': 0,
            'Defensiva Centro': 0,
            'Defensiva Derecha': 0,
            'Centro Izquierda': 0,
            'Centro Centro': 0,
            'Centro Derecha': 0,
            'Ofensiva Izquierda': 0,
            'Ofensiva Centro': 0,
            'Ofensiva Derecha': 0
        }
        
        for d in datos:
            x, y = d['posicion_x'], d['posicion_y']
            
            if x < 33:
                zona_x = 'Defensiva'
            elif x < 66:
                zona_x = 'Centro'
            else:
                zona_x = 'Ofensiva'
            
            if y < 33:
                zona_y = 'Izquierda'
            elif y < 66:
                zona_y = 'Centro'
            else:
                zona_y = 'Derecha'
            
            zona = f"{zona_x} {zona_y}"
            if zona in zonas:
                zonas[zona] += 1
        
        total = sum(zonas.values())
        if total > 0:
            return {zona: round((count / total) * 100, 1) for zona, count in zonas.items()}
        return zonas

# ============================================
# GESTOR DE JUGADORES DE FÚTBOL
# ============================================

class GestorFutbol:
    def __init__(self):
        self.data_file = 'datos_futbol.json'
        self.jugadores = {}
        self.entrenamientos = {}
        self.metricas = {}
        self.datos_medicos = {}
        self.load_data()
    
    def load_data(self):
        """Cargar datos de jugadores"""
        try:
            if os.path.exists(self.data_file):
                print(f"📂 Cargando datos desde {self.data_file}...")
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.jugadores = data.get('jugadores', {})
                    self.entrenamientos = data.get('entrenamientos', {})
                    self.metricas = data.get('metricas', {})
                    self.datos_medicos = data.get('datos_medicos', {})
                    print(f"✅ Datos cargados: {len(self.jugadores)} jugadores")
                    
                    # Verificar que los datos se cargaron correctamente
                    if self.jugadores:
                        print(f"   IDs de jugadores: {list(self.jugadores.keys())}")
            else:
                print(f"📂 Archivo {self.data_file} no encontrado, creando datos de ejemplo...")
                self.crear_datos_ejemplo()
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            import traceback
            traceback.print_exc()
            self.jugadores = {}
            self.entrenamientos = {}
            self.metricas = {}
            self.datos_medicos = {}
    
    def save_data(self):
        """Guardar todos los datos"""
        try:
            # Asegurar que la carpeta existe
            os.makedirs(os.path.dirname(self.data_file) if os.path.dirname(self.data_file) else '.', exist_ok=True)
            
            data = {
                'jugadores': self.jugadores,
                'entrenamientos': self.entrenamientos,
                'metricas': self.metricas,
                'datos_medicos': self.datos_medicos,
                'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Guardar con formato legible
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Datos guardados correctamente en {self.data_file}")
            print(f"   Total jugadores: {len(self.jugadores)}")
            return True
        except Exception as e:
            print(f"❌ Error guardando datos: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def crear_datos_ejemplo(self):
        """Crear jugadores de ejemplo para fútbol"""
        print("⚽ Creando equipo de fútbol de ejemplo...")
        
        # Jugadores por posición
        jugadores_ejemplo = [
            ['Marcos López', 'Portero', 28, 85, 188],
            ['Carlos García', 'Defensa Central', 25, 78, 183],
            ['Juan Martínez', 'Lateral Derecho', 24, 75, 180],
            ['Andrés Rodríguez', 'Lateral Izquierdo', 26, 76, 181],
            ['David Sánchez', 'Mediocentro Defensivo', 27, 77, 182],
            ['Miguel Torres', 'Mediocentro', 23, 74, 178],
            ['Jorge Ruiz', 'Mediocentro Ofensivo', 22, 73, 176],
            ['Luis Fernández', 'Extremo Derecho', 21, 72, 175],
            ['Pedro Gómez', 'Delantero Centro', 29, 82, 185],
            ['Sergio Díaz', 'Extremo Izquierdo', 20, 71, 174]
        ]
        
        for i, datos in enumerate(jugadores_ejemplo, 1):
            jugador_id = str(i)
            nombre, pos, edad, peso, altura = datos
            
            self.jugadores[jugador_id] = {
                'nombre': nombre,
                'posicion': pos,
                'numero': i,
                'edad': edad,
                'peso': peso,
                'altura': altura,
                'pie_habil': np.random.choice(['Derecho', 'Izquierdo', 'Ambidiestro']),
                'estado': 'Activo',
                'lesionado': False,
                'fecha_ingreso': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Generar datos iniciales
            pos_abrev = self._obtener_abreviatura_posicion(pos)
            self.generar_metricas_jugador(jugador_id, pos_abrev)
            self.generar_entrenamientos_jugador(jugador_id, pos_abrev)
            self.generar_datos_medicos(jugador_id, pos_abrev)
        
        # Generar algunos jugadores lesionados de ejemplo
        self.generar_lesiones_ejemplo()
        
        self.save_data()
        print(f"✅ Equipo creado con {len(self.jugadores)} jugadores")
    
    def generar_lesiones_ejemplo(self):
        """Generar jugadores lesionados de ejemplo"""
        # Hacer que 3 jugadores estén lesionados
        jugadores_ids = list(self.jugadores.keys())[:3]
        tipos_lesion = [
            {'tipo': 'Esguince de tobillo', 'tiempo_baja': '3-4 semanas'},
            {'tipo': 'Rotura fibrilar grado II', 'tiempo_baja': '6-8 semanas'},
            {'tipo': 'Pubalgia', 'tiempo_baja': '4-6 semanas'},
            {'tipo': 'Lesión de LCA', 'tiempo_baja': '6-9 meses'},
            {'tipo': 'Tendinitis aquilea', 'tiempo_baja': '2-3 semanas'},
            {'tipo': 'Contractura muscular', 'tiempo_baja': '1-2 semanas'}
        ]
        
        for i, jugador_id in enumerate(jugadores_ids):
            lesion = tipos_lesion[i % len(tipos_lesion)]
            self.jugadores[jugador_id]['lesionado'] = True
            self.jugadores[jugador_id]['estado'] = 'Lesionado'
            
            # Actualizar datos médicos
            if jugador_id in self.datos_medicos:
                self.datos_medicos[jugador_id]['lesion_actual'] = {
                    'tipo': lesion['tipo'],
                    'fecha_inicio': (datetime.now() - timedelta(days=np.random.randint(1, 10))).strftime('%Y-%m-%d'),
                    'tiempo_baja_estimado': lesion['tiempo_baja'],
                    'dias_transcurridos': np.random.randint(3, 10),
                    'recuperacion_estimada': (datetime.now() + timedelta(days=np.random.randint(14, 30))).strftime('%Y-%m-%d'),
                    'gravedad': 'Moderada' if 'semanas' in lesion['tiempo_baja'] else 'Grave'
                }
    
    def _obtener_abreviatura_posicion(self, posicion):
        """Convertir posición a abreviatura"""
        if 'Portero' in posicion or 'Arquero' in posicion:
            return 'POR'
        elif 'Defensa' in posicion:
            return 'DEF'
        elif 'Medio' in posicion or 'Centro' in posicion:
            return 'MED'
        else:
            return 'DEL'
    
    def generar_metricas_jugador(self, jugador_id, posicion):
        """Generar métricas específicas por posición"""
        if posicion == 'POR':  # Portero
            metricas = {
                'reflejos': np.random.randint(80, 95),
                'salto': np.random.randint(75, 90),
                'saque': np.random.randint(70, 85),
                'juego_aereo': np.random.randint(80, 95),
                'uno_contra_uno': np.random.randint(75, 90),
                'distribucion': np.random.randint(70, 85)
            }
        elif posicion == 'DEF':  # Defensa
            metricas = {
                'marcaje': np.random.randint(80, 95),
                'entrada': np.random.randint(75, 90),
                'anticipacion': np.random.randint(70, 85),
                'juego_aereo': np.random.randint(75, 90),
                'salida_balon': np.random.randint(70, 85),
                'resistencia': np.random.randint(80, 95)
            }
        elif posicion == 'MED':  # Mediocampista
            metricas = {
                'vision': np.random.randint(80, 95),
                'pase': np.random.randint(75, 90),
                'regate': np.random.randint(70, 85),
                'disparo_lejano': np.random.randint(75, 90),
                'recuperacion': np.random.randint(80, 95),
                'resistencia': np.random.randint(85, 95)
            }
        else:  # Delantero
            metricas = {
                'definicion': np.random.randint(80, 95),
                'disparo': np.random.randint(75, 90),
                'velocidad': np.random.randint(85, 95),
                'regate': np.random.randint(80, 95),
                'juego_aereo': np.random.randint(70, 85),
                'movimiento': np.random.randint(75, 90)
            }
        
        # Métricas físicas generales
        metricas.update({
            'frecuencia_reposo': np.random.randint(55, 70),
            'frecuencia_maxima': np.random.randint(185, 205),
            'vo2_max': round(np.random.uniform(45, 60), 1),
            'velocidad_maxima': round(np.random.uniform(28, 35), 1),
            'aceleracion_10m': round(np.random.uniform(1.7, 2.2), 2),
            'salto_vertical': round(np.random.uniform(45, 65), 1)
        })
        
        # Generar datos para mapa de calor real (coordenadas en campo)
        metricas['mapa_calor_datos'] = self.generar_datos_mapa_calor(posicion)
        
        self.metricas[jugador_id] = metricas
    
    def generar_datos_mapa_calor(self, posicion):
        """Generar datos reales para mapa de calor en campo de fútbol"""
        # Coordenadas del campo: x de 0 a 100, y de 0 a 100
        # 0,0 es esquina inferior izquierda, 100,100 esquina superior derecha
        
        datos = []
        num_puntos = 200
        
        if posicion == 'POR':
            # Portero: se mueve principalmente en área
            for _ in range(num_puntos):
                x = round(np.random.uniform(0, 20), 1)
                y = round(np.random.uniform(35, 65), 1)
                intensidad = round(np.random.uniform(0.7, 1.0), 2)
                datos.append({'x': x, 'y': y, 'intensidad': intensidad})
                
        elif posicion == 'DEF':
            # Defensa: zona defensiva
            for _ in range(num_puntos):
                x = round(np.random.uniform(0, 40), 1)
                y = round(np.random.uniform(10, 90), 1)
                intensidad = round(np.random.uniform(0.6, 0.9), 2)
                datos.append({'x': x, 'y': y, 'intensidad': intensidad})
                
        elif posicion == 'MED':
            # Mediocampista: todo el centro
            for _ in range(num_puntos):
                x = round(np.random.uniform(20, 80), 1)
                y = round(np.random.uniform(20, 80), 1)
                intensidad = round(np.random.uniform(0.5, 0.8), 2)
                datos.append({'x': x, 'y': y, 'intensidad': intensidad})
                
        else:  # DEL
            # Delantero: zona ofensiva
            for _ in range(num_puntos):
                x = round(np.random.uniform(60, 100), 1)
                y = round(np.random.uniform(20, 80), 1)
                intensidad = round(np.random.uniform(0.7, 1.0), 2)
                datos.append({'x': x, 'y': y, 'intensidad': intensidad})
        
        return datos
    
    def generar_entrenamientos_jugador(self, jugador_id, posicion):
        """Generar entrenamientos de los últimos 7 días"""
        entrenamientos = []
        
        for i in range(7):
            fecha = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
            
            if posicion == 'POR':
                distancia = round(np.random.uniform(3, 5), 1)
                sprints = np.random.randint(5, 15)
            elif posicion == 'DEF':
                distancia = round(np.random.uniform(8, 11), 1)
                sprints = np.random.randint(15, 25)
            elif posicion == 'MED':
                distancia = round(np.random.uniform(10, 13), 1)
                sprints = np.random.randint(20, 30)
            else:  # DEL
                distancia = round(np.random.uniform(9, 12), 1)
                sprints = np.random.randint(25, 35)
            
            entrenamientos.append({
                'fecha': fecha,
                'tipo': np.random.choice(['Técnico', 'Táctico', 'Físico', 'Partido']),
                'duracion': np.random.randint(60, 120),
                'distancia': distancia,
                'sprints': sprints,
                'carga': np.random.randint(300, 600),
                'fatiga': np.random.randint(3, 8),
                'frecuencia_max': np.random.randint(160, 195),
                'frecuencia_prom': np.random.randint(120, 150)
            })
        
        self.entrenamientos[jugador_id] = entrenamientos
    
    def generar_datos_medicos(self, jugador_id, posicion):
        """Generar datos médicos del jugador con tiempo de baja"""
        # Generar lesiones previas aleatorias
        lesiones_previas = np.random.randint(0, 4)
        historial_lesiones = []
        
        tipos_lesion_info = [
            {'tipo': 'Esguince de tobillo', 'tiempo_baja': '3-4 semanas'},
            {'tipo': 'Rotura fibrilar grado I', 'tiempo_baja': '2-3 semanas'},
            {'tipo': 'Rotura fibrilar grado II', 'tiempo_baja': '6-8 semanas'},
            {'tipo': 'Pubalgia', 'tiempo_baja': '4-6 semanas'},
            {'tipo': 'Lesión de rodilla (LCA)', 'tiempo_baja': '6-9 meses'},
            {'tipo': 'Tendinitis aquilea', 'tiempo_baja': '2-3 semanas'},
            {'tipo': 'Contractura muscular', 'tiempo_baja': '1-2 semanas'},
            {'tipo': 'Fractura por estrés', 'tiempo_baja': '8-12 semanas'},
            {'tipo': 'Conmoción cerebral', 'tiempo_baja': '2-4 semanas'},
            {'tipo': 'Desgarro muscular', 'tiempo_baja': '4-6 semanas'}
        ]
        
        for i in range(lesiones_previas):
            lesion_info = np.random.choice(tipos_lesion_info)
            fecha_lesion = (datetime.now() - timedelta(days=np.random.randint(30, 365))).strftime('%Y-%m-%d')
            duracion_dias = 7 if 'semanas' in lesion_info['tiempo_baja'] else 30
            
            historial_lesiones.append({
                'tipo': lesion_info['tipo'],
                'fecha': fecha_lesion,
                'duracion_dias': duracion_dias,
                'tiempo_baja': lesion_info['tiempo_baja'],
                'gravedad': np.random.choice(['Leve', 'Moderada', 'Grave']),
                'recuperacion_completa': np.random.choice([True, False])
            })
        
        self.datos_medicos[jugador_id] = {
            'ultimo_control': (datetime.now() - timedelta(days=np.random.randint(0, 30))).strftime('%Y-%m-%d'),
            'lesiones_previas': lesiones_previas,
            'historial_lesiones': historial_lesiones,
            'dias_lesionado': 0,
            'estado_fisico': np.random.choice(['Óptimo', 'Bueno', 'Regular']),
            'observaciones': 'Sin observaciones',
            'lesion_actual': None
        }
    
    # ========== OPERACIONES CRUD ==========
    
    def agregar_jugador(self, datos):
        """Agregar nuevo jugador al equipo"""
        try:
            # Validar datos obligatorios
            if not datos.get('nombre') or not datos.get('posicion'):
                print("❌ Nombre y posición son obligatorios")
                return None
            
            # Obtener nuevo ID
            if self.jugadores:
                # Convertir IDs a enteros para encontrar el máximo
                ids_numericos = []
                for k in self.jugadores.keys():
                    try:
                        ids_numericos.append(int(k))
                    except:
                        pass
                nuevo_id = str(max(ids_numericos) + 1) if ids_numericos else "1"
            else:
                nuevo_id = "1"
            
            print(f"📝 Agregando jugador con ID: {nuevo_id}")
            print(f"📝 Datos recibidos: {datos}")
            
            # Crear el jugador
            self.jugadores[nuevo_id] = {
                'nombre': datos['nombre'],
                'posicion': datos['posicion'],
                'numero': datos.get('numero', 0),
                'edad': int(datos.get('edad', 25)),
                'peso': float(datos.get('peso', 70)),
                'altura': int(datos.get('altura', 175)),
                'pie_habil': datos.get('pie_habil', 'Derecho'),
                'estado': 'Activo',
                'lesionado': False,
                'fecha_ingreso': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Generar datos iniciales
            pos_abrev = self._obtener_abreviatura_posicion(datos['posicion'])
            self.generar_metricas_jugador(nuevo_id, pos_abrev)
            self.generar_entrenamientos_jugador(nuevo_id, pos_abrev)
            self.generar_datos_medicos(nuevo_id, pos_abrev)
            
            # Guardar datos INMEDIATAMENTE
            if self.save_data():
                print(f"✅ Jugador {datos['nombre']} agregado exitosamente con ID {nuevo_id}")
                return nuevo_id
            else:
                print("❌ Error al guardar datos después de agregar jugador")
                # Si falla el guardado, eliminar el jugador de la memoria
                del self.jugadores[nuevo_id]
                return None
                
        except Exception as e:
            print(f"❌ Error al agregar jugador: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def eliminar_jugador(self, jugador_id):
        """Eliminar jugador del equipo"""
        if jugador_id in self.jugadores:
            nombre = self.jugadores[jugador_id]['nombre']
            
            # Eliminar todos los datos del jugador
            del self.jugadores[jugador_id]
            
            if jugador_id in self.entrenamientos:
                del self.entrenamientos[jugador_id]
            
            if jugador_id in self.metricas:
                del self.metricas[jugador_id]
            
            if jugador_id in self.datos_medicos:
                del self.datos_medicos[jugador_id]
            
            # Guardar cambios
            if self.save_data():
                print(f"✅ Jugador {nombre} eliminado exitosamente")
                return True
            else:
                print("❌ Error al guardar después de eliminar")
                return False
        return False
    
    def obtener_jugador(self, jugador_id):
        """Obtener información completa de un jugador"""
        if jugador_id not in self.jugadores:
            print(f"Jugador {jugador_id} no encontrado")
            return None
        
        try:
            datos = {
                'info': self.jugadores.get(jugador_id, {}),
                'metricas': self.metricas.get(jugador_id, {}),
                'entrenamientos': self.entrenamientos.get(jugador_id, []),
                'medico': self.datos_medicos.get(jugador_id, {})
            }
            
            # Verificar que todos los datos existan
            if not datos['info']:
                print(f"Información básica no encontrada para jugador {jugador_id}")
                return None
                
            # Si no hay métricas, generarlas
            if not datos['metricas']:
                print(f"Generando métricas para jugador {jugador_id}")
                pos_abrev = self._obtener_abreviatura_posicion(datos['info']['posicion'])
                self.generar_metricas_jugador(jugador_id, pos_abrev)
                datos['metricas'] = self.metricas.get(jugador_id, {})
                
            # Si no hay entrenamientos, generarlos
            if not datos['entrenamientos']:
                print(f"Generando entrenamientos para jugador {jugador_id}")
                pos_abrev = self._obtener_abreviatura_posicion(datos['info']['posicion'])
                self.generar_entrenamientos_jugador(jugador_id, pos_abrev)
                datos['entrenamientos'] = self.entrenamientos.get(jugador_id, [])
                
            # Si no hay datos médicos, generarlos
            if not datos['medico']:
                print(f"Generando datos médicos para jugador {jugador_id}")
                pos_abrev = self._obtener_abreviatura_posicion(datos['info']['posicion'])
                self.generar_datos_medicos(jugador_id, pos_abrev)
                datos['medico'] = self.datos_medicos.get(jugador_id, {})
            
            return datos
        except Exception as e:
            print(f"Error obteniendo datos del jugador {jugador_id}: {e}")
            return None
    
    def obtener_todos_jugadores(self):
        """Obtener lista de todos los jugadores"""
        return self.jugadores
    
    def calcular_estadisticas_equipo(self):
        """Calcular estadísticas generales del equipo"""
        if not self.jugadores:
            return {}
        
        total_jugadores = len(self.jugadores)
        activos = sum(1 for j in self.jugadores.values() if j['estado'] == 'Activo')
        lesionados = sum(1 for j in self.jugadores.values() if j['lesionado'])
        
        # Promedios de edad, peso, altura
        edades = [j['edad'] for j in self.jugadores.values()]
        pesos = [j['peso'] for j in self.jugadores.values()]
        alturas = [j['altura'] for j in self.jugadores.values()]
        
        return {
            'total_jugadores': total_jugadores,
            'activos': activos,
            'lesionados': lesionados,
            'edad_promedio': round(np.mean(edades), 1) if edades else 0,
            'peso_promedio': round(np.mean(pesos), 1) if pesos else 0,
            'altura_promedio': round(np.mean(alturas), 1) if alturas else 0,
            'distribucion_posiciones': self._contar_posiciones()
        }
    
    def _contar_posiciones(self):
        """Contar jugadores por posición"""
        conteo = {}
        for jugador in self.jugadores.values():
            pos = jugador['posicion']
            conteo[pos] = conteo.get(pos, 0) + 1
        return conteo
    
    def obtener_analisis_lesiones(self):
        """Obtener análisis completo de lesiones del equipo"""
        if not self.jugadores:
            return {}
        
        total_lesiones = 0
        lesiones_por_posicion = {}
        tipos_lesion = {}
        jugadores_lesionados = []
        
        for jugador_id, jugador in self.jugadores.items():
            datos_medicos = self.datos_medicos.get(jugador_id, {})
            pos = jugador['posicion']
            
            # Contar lesiones
            lesiones_jugador = datos_medicos.get('lesiones_previas', 0)
            total_lesiones += lesiones_jugador
            
            # Por posición
            if pos not in lesiones_por_posicion:
                lesiones_por_posicion[pos] = 0
            lesiones_por_posicion[pos] += lesiones_jugador
            
            # Tipos de lesión
            historial = datos_medicos.get('historial_lesiones', [])
            for lesion in historial:
                tipo = lesion.get('tipo', 'Desconocido')
                tipos_lesion[tipo] = tipos_lesion.get(tipo, 0) + 1
            
            # Jugadores lesionados actualmente
            if jugador.get('lesionado', False):
                lesion_actual = datos_medicos.get('lesion_actual', {})
                jugadores_lesionados.append({
                    'nombre': jugador['nombre'],
                    'posicion': pos,
                    'numero': jugador['numero'],
                    'tipo_lesion': lesion_actual.get('tipo', 'No especificada') if lesion_actual else 'No especificada',
                    'tiempo_baja': lesion_actual.get('tiempo_baja_estimado', 'N/A') if lesion_actual else 'N/A',
                    'dias_lesionado': lesion_actual.get('dias_transcurridos', 0) if lesion_actual else 0
                })
        
        return {
            'total_lesiones': total_lesiones,
            'lesiones_por_posicion': lesiones_por_posicion,
            'tipos_lesion_mas_comunes': dict(sorted(tipos_lesion.items(), key=lambda x: x[1], reverse=True)[:5]),
            'jugadores_lesionados_actualmente': jugadores_lesionados,
            'tasa_lesiones_por_jugador': round(total_lesiones / len(self.jugadores), 2) if self.jugadores else 0
        }
    
    def obtener_resumen_rendimiento(self):
        """Obtener resumen del rendimiento del equipo"""
        estadisticas = self.calcular_estadisticas_equipo()
        
        # Calcular puntuación promedio del equipo
        puntuaciones = []
        for jugador_id in self.jugadores.keys():
            metricas = self.metricas.get(jugador_id, {})
            if metricas:
                # Calcular puntuación promedio del jugador
                valores = [v for k, v in metricas.items() if isinstance(v, (int, float)) and 'mapa_calor' not in k]
                if valores:
                    puntuaciones.append(np.mean(valores))
        
        # Análisis por posición
        analisis_posiciones = {}
        for pos in set(j['posicion'] for j in self.jugadores.values()):
            jugadores_pos = [j for j in self.jugadores.values() if j['posicion'] == pos]
            analisis_posiciones[pos] = {
                'cantidad': len(jugadores_pos),
                'edad_promedio': round(np.mean([j['edad'] for j in jugadores_pos]), 1) if jugadores_pos else 0,
                'estado': {
                    'activos': sum(1 for j in jugadores_pos if not j.get('lesionado', False)),
                    'lesionados': sum(1 for j in jugadores_pos if j.get('lesionado', False))
                }
            }
        
        return {
            'puntuacion_promedio_equipo': round(np.mean(puntuaciones), 2) if puntuaciones else 0,
            'mejor_valorado': self._obtener_mejor_valorado(),
            'analisis_posiciones': analisis_posiciones,
            'estadisticas_generales': estadisticas
        }
    
    def _obtener_mejor_valorado(self):
        """Obtener el jugador mejor valorado"""
        mejor_jugador = None
        mejor_puntuacion = 0
        
        for jugador_id, jugador in self.jugadores.items():
            metricas = self.metricas.get(jugador_id, {})
            if metricas:
                valores = [v for k, v in metricas.items() if isinstance(v, (int, float)) and 'mapa_calor' not in k]
                if valores:
                    puntuacion = np.mean(valores)
                    if puntuacion > mejor_puntuacion:
                        mejor_puntuacion = puntuacion
                        mejor_jugador = {
                            'id': jugador_id,
                            'nombre': jugador['nombre'],
                            'posicion': jugador['posicion'],
                            'numero': jugador['numero'],
                            'puntuacion': round(puntuacion, 2)
                        }
        
        return mejor_jugador
    

# ============================================
# INICIALIZACIÓN DEL SISTEMA
# ============================================
auth_system = AuthSystem()
gestor_futbol = GestorFutbol()
simulador_sensores = SensorSimulador(gestor_futbol)

# ============================================
# APLICACIÓN DASH
# ============================================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Fútbol Pro Analytics - Sistema de Simulación"
server = app.server

# ============================================
# ESTILOS CSS PARA FÚTBOL (CON SIMULADOR)
# ============================================
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Fútbol Pro Analytics - Sistema de Simulación</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --color-primario: #1e3c72;
                --color-secundario: #2a5298;
                --color-exito: #10b981;
                --color-peligro: #ef4444;
                --color-advertencia: #f59e0b;
                --color-info: #3b82f6;
                --color-simulacion: #8b5cf6;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%);
                min-height: 100vh;
                color: #333;
            }
            
            /* Login */
            .login-container {
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }
            
            .login-card {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                width: 100%;
                max-width: 400px;
                border: 3px solid #1e3c72;
            }
            
            .login-logo {
                text-align: center;
                font-size: 2.5rem;
                margin-bottom: 10px;
                color: #1e3c72;
            }
            
            .login-title {
                text-align: center;
                font-size: 1.8rem;
                font-weight: bold;
                color: #1e3c72;
                margin-bottom: 5px;
            }
            
            .login-subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
                font-size: 0.9rem;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #444;
            }
            
            .form-input {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: all 0.3s;
            }
            
            .form-input:focus {
                outline: none;
                border-color: #1e3c72;
                box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
            }
            
            .btn {
                padding: 14px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                width: 100%;
            }
            
            .btn-primary {
                background: linear-gradient(to right, #1e3c72, #2a5298);
                color: white;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(30, 60, 114, 0.3);
            }
            
            .btn-success {
                background: linear-gradient(to right, #10b981, #34d399);
                color: white;
            }
            
            .btn-danger {
                background: linear-gradient(to right, #ef4444, #f87171);
                color: white;
            }
            
            .btn-warning {
                background: linear-gradient(to right, #f59e0b, #fbbf24);
                color: white;
            }
            
            .btn-info {
                background: linear-gradient(to right, #3b82f6, #60a5fa);
                color: white;
            }
            
            .btn-simulacion {
                background: linear-gradient(to right, #8b5cf6, #a78bfa);
                color: white;
            }
            
            .btn-simulacion:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(139, 92, 246, 0.3);
            }
            
            .alert {
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                font-weight: 500;
            }
            
            .alert-success {
                background: #d1fae5;
                color: #065f46;
                border: 1px solid #a7f3d0;
            }
            
            .alert-error {
                background: #fee2e2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }
            
            .alert-simulacion {
                background: #ede9fe;
                color: #5b21b6;
                border: 1px solid #ddd6fe;
                border-left: 4px solid #8b5cf6;
            }
            
            /* Layout Principal */
            .app-header {
                background: white;
                padding: 15px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-bottom: 3px solid #1e3c72;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .header-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 1.5rem;
                font-weight: bold;
                color: #1e3c72;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .header-buttons {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .main-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                min-height: calc(100vh - 120px);
            }
            
            /* Dashboard Grid */
            .dashboard-grid {
                display: grid;
                gap: 20px;
                min-height: calc(100vh - 180px);
            }
            
            /* Sidebar */
            .sidebar {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .sidebar-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #e5e7eb;
            }
            
            /* Tarjetas de Jugador */
            .jugador-card {
                background: #f8fafc;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                cursor: pointer;
                transition: all 0.3s;
                border-left: 4px solid #1e3c72;
                position: relative;
                width: 100%;
            }
            
            .jugador-card:hover {
                transform: translateX(5px);
                background: #eef2ff;
            }
            
            .jugador-card.active {
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                color: white;
            }
            
            .jugador-card:hover .btn-eliminar {
                display: block !important;
            }
            
            .jugador-nombre {
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .jugador-info {
                font-size: 0.85rem;
                color: #666;
            }
            
            .jugador-card.active .jugador-info {
                color: rgba(255,255,255,0.9);
            }
            
            .badge-posicion {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 15px;
                font-size: 0.75rem;
                font-weight: 600;
                margin-left: 5px;
            }
            
            .badge-POR { background: #fbbf24; color: #78350f; }
            .badge-DEF { background: #10b981; color: #064e3b; }
            .badge-MED { background: #3b82f6; color: #1e3a8a; }
            .badge-DEL { background: #ef4444; color: #7f1d1d; }
            
            /* Contenido Principal */
            .content {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                width: 100%;
                position: relative;
            }
            
            /* Estadísticas */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 25px;
            }
            
            .stat-card {
                background: #f8fafc;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                border-top: 4px solid #1e3c72;
            }
            
            .stat-valor {
                font-size: 2rem;
                font-weight: bold;
                color: #1e3c72;
                margin-bottom: 5px;
            }
            
            .stat-label {
                color: #666;
                font-size: 0.9rem;
            }
            
            /* Pestañas */
            .tabs-container {
                margin-top: 20px;
            }
            
            .tab-content {
                padding: 20px 0;
            }
            
            /* Gráficos */
            .graph-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                border: 1px solid #e5e7eb;
            }
            
            /* Métricas */
            .metricas-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            
            .metrica-item {
                background: #f8fafc;
                padding: 15px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .metrica-nombre {
                font-weight: 500;
                color: #444;
            }
            
            .metrica-valor {
                font-weight: bold;
                color: #1e3c72;
            }
            
            /* Modal */
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                align-items: center;
                justify-content: center;
            }
            
            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 10px;
                width: 90%;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
            }
            
            /* Estado de lesión */
            .estado-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
            }
            
            .estado-activo { background: #d1fae5; color: #065f46; }
            .estado-lesionado { background: #fee2e2; color: #dc2626; }
            .estado-descanso { background: #fef3c7; color: #92400e; }
            .estado-simulando { background: #ede9fe; color: #5b21b6; }
            
            /* Campo de fútbol */
            .campo-futbol {
                width: 100%;
                height: 500px;
                background: #4ade80;
                border: 2px solid white;
                border-radius: 5px;
                position: relative;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .campo-lines {
                position: absolute;
                width: 100%;
                height: 100%;
                border: 2px solid white;
            }
            
            /* Panel de simulación */
            .panel-simulacion {
                background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                border: 2px solid #8b5cf6;
            }
            
            .simulacion-estadisticas {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            
            .simulacion-estadistica {
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .simulacion-valor {
                font-size: 1.5rem;
                font-weight: bold;
                color: #8b5cf6;
                margin-bottom: 5px;
            }
            
            .simulacion-label {
                color: #666;
                font-size: 0.9rem;
            }
            
            /* Indicadores de tiempo real */
            .indicador-tiempo-real {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 1.5s infinite;
            }
            
            .indicador-activo {
                background-color: #10b981;
            }
            
            .indicador-inactivo {
                background-color: #ef4444;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }
            
            /* Responsive */
            @media (max-width: 1024px) {
                .dashboard-grid {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    height: auto !important;
                    position: relative !important;
                }
                
                .content {
                    height: auto !important;
                }
                
                #lista-jugadores {
                    height: auto !important;
                    max-height: 300px;
                }
                
                .header-buttons {
                    flex-direction: column;
                    gap: 5px;
                }
            }
            
            @media (min-width: 1025px) {
                .dashboard-grid {
                    grid-template-columns: 300px 1fr;
                }
            }
            
            /* Botón eliminar */
            .btn-eliminar {
                background: #ef4444;
                color: white;
                border: none;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 12px;
                display: none;
                padding: 0;
                line-height: 1;
                position: absolute;
                right: 10px;
                top: 10px;
            }
            
            .btn-eliminar:hover {
                background: #dc2626;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================================
# FUNCIONES AUXILIARES (ACTUALIZADAS CON SIMULADOR)
# ============================================
def crear_campo_futbol_con_mapa_calor(datos_mapa_calor):
    """Crear gráfico de campo de fútbol con mapa de calor"""
    if not datos_mapa_calor:
        return go.Figure()
    
    # Extraer datos
    x = [p['x'] for p in datos_mapa_calor]
    y = [p['y'] for p in datos_mapa_calor]
    intensidad = [p['intensidad'] for p in datos_mapa_calor]
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir mapa de calor
    fig.add_trace(go.Histogram2dContour(
        x=x,
        y=y,
        z=intensidad,
        colorscale='Hot',
        showscale=True,
        line_width=0,
        ncontours=20,
        contours=dict(
            coloring='heatmap',
            showlabels=True
        ),
        hoverinfo='none'
    ))
    
    # Añadir puntos dispersos
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=5,
            color=intensidad,
            colorscale='Hot',
            showscale=False,
            opacity=0.3
        ),
        hoverinfo='none'
    ))
    
    # Dibujar líneas del campo
    # Líneas exteriores
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=100, y1=100,
        line=dict(color="white", width=3),
        fillcolor="rgba(0,0,0,0)"
    )
    
    # Línea central
    fig.add_shape(type="line",
        x0=50, y0=0, x1=50, y1=100,
        line=dict(color="white", width=2, dash="dash")
    )
    
    # Círculo central
    fig.add_shape(type="circle",
        x0=40, y0=40, x1=60, y1=60,
        line=dict(color="white", width=2)
    )
    
    # Área izquierda
    fig.add_shape(type="rect",
        x0=0, y0=25, x1=16, y1=75,
        line=dict(color="white", width=2)
    )
    
    # Área derecha
    fig.add_shape(type="rect",
        x0=84, y0=25, x1=100, y1=75,
        line=dict(color="white", width=2)
    )
    
    # Área pequeña izquierda
    fig.add_shape(type="rect",
        x0=0, y0=40, x1=5, y1=60,
        line=dict(color="white", width=2)
    )
    
    # Área pequeña derecha
    fig.add_shape(type="rect",
        x0=95, y0=40, x1=100, y1=60,
        line=dict(color="white", width=2)
    )
    
    # Punto penal izquierdo
    fig.add_trace(go.Scatter(
        x=[11], y=[50],
        mode='markers',
        marker=dict(size=10, color='white'),
        hoverinfo='none'
    ))
    
    # Punto penal derecho
    fig.add_trace(go.Scatter(
        x=[89], y=[50],
        mode='markers',
        marker=dict(size=10, color='white'),
        hoverinfo='none'
    ))
    
    # Punto central
    fig.add_trace(go.Scatter(
        x=[50], y=[50],
        mode='markers',
        marker=dict(size=10, color='white'),
        hoverinfo='none'
    ))
    
    # Actualizar layout
    fig.update_layout(
        title='Mapa de Calor - Distribución en el Campo',
        xaxis=dict(
            range=[0, 100],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            scaleanchor="x",
            scaleratio=0.7,
            range=[0, 100],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='#4ade80',
        paper_bgcolor='white',
        height=500,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def generar_detalles_lesiones_jugador(datos_medicos):
    """Generar tabla de detalles de lesiones con tiempo de baja"""
    historial = datos_medicos.get('historial_lesiones', [])
    lesion_actual = datos_medicos.get('lesion_actual', {})
    
    if not historial and not lesion_actual:
        return html.P("No hay historial de lesiones", style={'color': '#666', 'textAlign': 'center', 'padding': '20px'})
    
    rows = []
    
    # Agregar lesión actual si existe
    if lesion_actual:
        rows.append(html.Tr([
            html.Td(lesion_actual.get('tipo', 'N/A'), style={'fontWeight': 'bold', 'color': '#dc2626'}),
            html.Td(lesion_actual.get('fecha_inicio', 'N/A')),
            html.Td(f"{lesion_actual.get('dias_transcurridos', 0)} días"),
            html.Td(lesion_actual.get('tiempo_baja_estimado', 'N/A'), style={'fontWeight': 'bold'}),
            html.Td(lesion_actual.get('gravedad', 'N/A')),
            html.Td(lesion_actual.get('recuperacion_estimada', 'N/A'))
        ]))
    
    # Agregar historial
    for lesion in historial:
        rows.append(html.Tr([
            html.Td(lesion.get('tipo', 'N/A')),
            html.Td(lesion.get('fecha', 'N/A')),
            html.Td(f"{lesion.get('duracion_dias', 0)} días"),
            html.Td(lesion.get('tiempo_baja', 'N/A')),
            html.Td(lesion.get('gravedad', 'N/A')),
            html.Td("Completa" if lesion.get('recuperacion_completa', False) else "Incompleta")
        ]))
    
    return html.Table([
        html.Thead(
            html.Tr([
                html.Th("Tipo de Lesión"),
                html.Th("Fecha Inicio"),
                html.Th("Duración Real"),
                html.Th("Tiempo de Baja"),
                html.Th("Gravedad"),
                html.Th("Estado Recuperación")
            ])
        ),
        html.Tbody(rows)
    ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginTop': '20px'})

def crear_grafico_tiempo_real(datos):
    """Crear gráfico en tiempo real de los sensores"""
    if not datos:
        return go.Figure()
    
    tiempos = [d['minuto'] for d in datos]
    
    fig = go.Figure()
    
    # Velocidad
    fig.add_trace(go.Scatter(
        x=tiempos,
        y=[d['velocidad'] for d in datos],
        name='Velocidad (km/h)',
        line=dict(color='blue', width=2)
    ))
    
    # Frecuencia cardíaca
    fig.add_trace(go.Scatter(
        x=tiempos,
        y=[d['frecuencia_cardiaca'] for d in datos],
        name='Frecuencia Cardíaca (lpm)',
        yaxis='y2',
        line=dict(color='red', width=2)
    ))
    
    # Aceleración
    fig.add_trace(go.Scatter(
        x=tiempos,
        y=[d['aceleracion'] for d in datos],
        name='Aceleración (m/s²)',
        yaxis='y3',
        line=dict(color='green', width=2)
    ))
    
    # Fatiga
    fig.add_trace(go.Scatter(
        x=tiempos,
        y=[d['fatiga'] for d in datos],
        name='Fatiga (1-10)',
        yaxis='y4',
        line=dict(color='orange', width=2)
    ))
    
    fig.update_layout(
        title='📊 Datos en Tiempo Real',
        yaxis=dict(
            title='Velocidad (km/h)',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue'),
            range=[0, 15]
        ),
        yaxis2=dict(
            title='Frecuencia (lpm)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            overlaying='y',
            side='right',
            range=[60, 200]
        ),
        yaxis3=dict(
            title='Aceleración',
            titlefont=dict(color='green'),
            tickfont=dict(color='green'),
            overlaying='y',
            side='right',
            position=0.85,
            range=[0, 6]
        ),
        yaxis4=dict(
            title='Fatiga',
            titlefont=dict(color='orange'),
            tickfont=dict(color='orange'),
            overlaying='y',
            side='right',
            position=0.75,
            range=[0, 10]
        ),
        xaxis=dict(title='Minuto del Partido'),
        height=400,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def crear_mapa_calor_tiempo_real(datos):
    """Crear mapa de calor en tiempo real de la posición del jugador"""
    if not datos:
        return go.Figure()
    
    # Extraer las últimas posiciones
    posiciones_x = [d['posicion_x'] for d in datos]
    posiciones_y = [d['posicion_y'] for d in datos]
    
    fig = go.Figure()
    
    # Añadir puntos de posición
    fig.add_trace(go.Scatter(
        x=posiciones_x,
        y=posiciones_y,
        mode='markers+lines',
        marker=dict(
            size=8,
            color=list(range(len(posiciones_x))),
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Tiempo')
        ),
        line=dict(color='rgba(0,0,0,0.3)', width=1),
        name='Trayectoria'
    ))
    
    # Dibujar líneas del campo
    # Líneas exteriores
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=100, y1=100,
        line=dict(color="white", width=3),
        fillcolor="rgba(0,0,0,0)"
    )
    
    # Línea central
    fig.add_shape(type="line",
        x0=50, y0=0, x1=50, y1=100,
        line=dict(color="white", width=2, dash="dash")
    )
    
    # Círculo central
    fig.add_shape(type="circle",
        x0=40, y0=40, x1=60, y1=60,
        line=dict(color="white", width=2)
    )
    
    # Áreas
    fig.add_shape(type="rect",
        x0=0, y0=25, x1=16, y1=75,
        line=dict(color="white", width=2)
    )
    
    fig.add_shape(type="rect",
        x0=84, y0=25, x1=100, y1=75,
        line=dict(color="white", width=2)
    )
    
    # Puntos
    fig.add_trace(go.Scatter(
        x=[11, 50, 89],
        y=[50, 50, 50],
        mode='markers',
        marker=dict(size=10, color='white'),
        name='Puntos'
    ))
    
    fig.update_layout(
        title='📍 Posición en Tiempo Real',
        xaxis=dict(
            range=[0, 100],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            scaleanchor="x",
            scaleratio=0.7,
            range=[0, 100],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='#4ade80',
        paper_bgcolor='white',
        height=400,
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# ============================================
# LAYOUT PRINCIPAL (ACTUALIZADO CON SIMULADOR)
# ============================================
app.layout = html.Div([
    dcc.Store(id='usuario-actual', data=None),
    dcc.Store(id='jugador-seleccionado', data=None),
    dcc.Store(id='vista-activa', data='equipo'),
    dcc.Store(id='store-jugador-eliminar', data=None),
    dcc.Store(id='login-tab-activo', data='login'),
    dcc.Store(id='datos-simulacion', data=None),
    
    # Modal para nuevo jugador
    html.Div([
        html.Div([
            html.Div([
                html.H2("➕ Agregar Nuevo Jugador"),
                html.Button("×", id='btn-cerrar-modal', className='close-btn', 
                          style={'background': 'none', 'border': 'none', 'fontSize': '1.5rem', 'cursor': 'pointer'})
            ], className='modal-header', style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
            
            html.Div([
                html.Div([
                    html.Label("Nombre Completo *", className='form-label'),
                    dcc.Input(id='input-nombre', type='text', className='form-input', 
                             placeholder='Ej: Lionel Messi')
                ], className='form-group'),
                
                html.Div([
                    html.Label("Posición *", className='form-label'),
                    dcc.Dropdown(
                        id='input-posicion',
                        options=[
                            {'label': 'Portero', 'value': 'Portero'},
                            {'label': 'Defensa Central', 'value': 'Defensa Central'},
                            {'label': 'Lateral Derecho', 'value': 'Lateral Derecho'},
                            {'label': 'Lateral Izquierdo', 'value': 'Lateral Izquierdo'},
                            {'label': 'Mediocentro Defensivo', 'value': 'Mediocentro Defensivo'},
                            {'label': 'Mediocentro', 'value': 'Mediocentro'},
                            {'label': 'Mediocentro Ofensivo', 'value': 'Mediocentro Ofensivo'},
                            {'label': 'Extremo Derecho', 'value': 'Extremo Derecho'},
                            {'label': 'Delantero Centro', 'value': 'Delantero Centro'},
                            {'label': 'Extremo Izquierdo', 'value': 'Extremo Izquierdo'}
                        ],
                        value='Mediocentro',
                        className='form-input'
                    )
                ], className='form-group'),
                
                html.Div([
                    html.Label("Número de Camiseta", className='form-label'),
                    dcc.Input(id='input-numero', type='number', className='form-input', 
                             placeholder='10', min=1, max=99)
                ], className='form-group'),
                
                html.Div([
                    html.Label("Edad *", className='form-label'),
                    dcc.Input(id='input-edad', type='number', className='form-input', 
                             placeholder='25', min=16, max=45)
                ], className='form-group'),
                
                html.Div([
                    html.Label("Peso (kg) *", className='form-label'),
                    dcc.Input(id='input-peso', type='number', className='form-input', 
                             placeholder='75', min=50, max=120, step=0.1)
                ], className='form-group'),
                
                html.Div([
                    html.Label("Altura (cm) *", className='form-label'),
                    dcc.Input(id='input-altura', type='number', className='form-input', 
                             placeholder='180', min=160, max=210)
                ], className='form-group'),
                
                html.Div([
                    html.Label("Pie Hábil", className='form-label'),
                    dcc.Dropdown(
                        id='input-pie',
                        options=[
                            {'label': 'Derecho', 'value': 'Derecho'},
                            {'label': 'Izquierdo', 'value': 'Izquierdo'},
                            {'label': 'Ambidiestro', 'value': 'Ambidiestro'}
                        ],
                        value='Derecho',
                        className='form-input'
                    )
                ], className='form-group'),
            ]),
            
            html.Div([
                html.Button("Cancelar", id='btn-cancelar', className='btn', 
                          style={'background': '#6b7280', 'marginRight': '10px'}),
                html.Button("Agregar Jugador", id='btn-guardar-jugador', className='btn btn-primary')
            ], style={'display': 'flex', 'justifyContent': 'flex-end', 'marginTop': '20px'})
        ], className='modal-content')
    ], id='modal-nuevo-jugador', className='modal', style={'display': 'none'}),
    
    # Modal para eliminar jugador
    html.Div([
        html.Div([
            html.Div([
                html.H2("🗑️ Eliminar Jugador"),
                html.Button("×", id='btn-cerrar-modal-eliminar', 
                          style={'background': 'none', 'border': 'none', 'fontSize': '1.5rem', 'cursor': 'pointer'})
            ], className='modal-header', style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
            
            html.Div([
                html.P("¿Estás seguro de que quieres eliminar este jugador?"),
                html.P("Todos sus datos se perderán permanentemente.", style={'color': '#666', 'marginTop': '10px'}),
                html.P(id='nombre-jugador-eliminar', style={'fontWeight': 'bold', 'marginTop': '15px', 'color': '#1e3c72', 'fontSize': '1.1rem'})
            ]),
            
            html.Div([
                html.Button("Cancelar", id='btn-cancelar-eliminar', className='btn', 
                          style={'background': '#6b7280', 'marginRight': '10px'}),
                html.Button("Eliminar", id='btn-confirmar-eliminar', className='btn btn-danger')
            ], style={'display': 'flex', 'justifyContent': 'flex-end', 'marginTop': '20px'})
        ], className='modal-content')
    ], id='modal-eliminar-jugador', className='modal', style={'display': 'none'}),
    
    # Panel de alertas (para simulación)
    html.Div(id='panel-alertas', 
            style={'position': 'fixed', 'top': '80px', 'right': '20px', 
                   'width': '300px', 'zIndex': '1000'}),
    
    # Contenido principal
    html.Div(id='pagina-contenido')
])

# ============================================
# PÁGINAS (ACTUALIZADAS CON SIMULADOR)
# ============================================
def generar_pagina_login():
    """Generar página de login"""
    return html.Div([
        html.Div([
            html.Div([
                html.Div("⚽", className='login-logo'),
                html.H1("Fútbol Pro Analytics", className='login-title'),
                html.P("Sistema de Gestión y Simulación para Equipos de Fútbol", className='login-subtitle'),
                
                html.Div([
                    html.Div([
                        html.Label("Usuario", className='form-label'),
                        dcc.Input(id='login-username', type='text', className='form-input', 
                                 placeholder='entrenador')
                    ], className='form-group'),
                    
                    html.Div([
                        html.Label("Contraseña", className='form-label'),
                        dcc.Input(id='login-password', type='password', className='form-input', 
                                 placeholder='entrenador123')
                    ], className='form-group'),
                    
                    html.Button("Iniciar Sesión", id='btn-login', className='btn btn-primary'),
                    
                    html.Div(id='login-alert', style={'marginTop': '15px'})
                ]),
                
                html.Hr(style={'margin': '30px 0', 'border': 'none', 'borderTop': '1px solid #e5e7eb'}),
                
                html.Div([
                    html.P("¿No tienes cuenta? Regístrate como entrenador:", style={'textAlign': 'center', 'marginBottom': '15px'}),
                    
                    html.Div([
                        html.Label("Nombre Completo", className='form-label'),
                        dcc.Input(id='register-nombre', type='text', className='form-input', 
                                 placeholder='Tu nombre')
                    ], className='form-group'),
                    
                    html.Div([
                        html.Label("Usuario", className='form-label'),
                        dcc.Input(id='register-username', type='text', className='form-input', 
                                 placeholder='nombre_usuario')
                    ], className='form-group'),
                    
                    html.Div([
                        html.Label("Email", className='form-label'),
                        dcc.Input(id='register-email', type='email', className='form-input', 
                                 placeholder='correo@club.com')
                    ], className='form-group'),
                    
                    html.Div([
                        html.Label("Club", className='form-label'),
                        dcc.Input(id='register-club', type='text', className='form-input', 
                                 placeholder='Nombre del club')
                    ], className='form-group'),
                    
                    html.Div([
                        html.Label("Contraseña", className='form-label'),
                        dcc.Input(id='register-password', type='password', className='form-input', 
                                 placeholder='Mínimo 6 caracteres')
                    ], className='form-group'),
                    
                    html.Button("Registrarse", id='btn-register', className='btn btn-success'),
                    
                    html.Div(id='register-alert', style={'marginTop': '15px'})
                ])
            ], className='login-card')
        ], className='login-container')
    ])

def generar_pagina_principal(usuario):
    """Generar página principal después del login"""
    return html.Div([
        # Header
        html.Header([
            html.Div([
                html.Div([
                    html.Span("⚽ ", style={'fontSize': '1.8rem'}),
                    html.Span("Fútbol Pro Analytics", className='logo'),
                    html.Span("🎮", style={'fontSize': '1.2rem', 'color': '#8b5cf6', 'marginLeft': '5px'})
                ]),
                
                html.Div([
                    html.Button("🏆 Mi Equipo", id='btn-vista-equipo', 
                              style={'background': '#1e3c72', 'color': 'white', 'padding': '8px 16px', 
                                     'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': '500', 'marginRight': '10px'}),
                    html.Button("📊 Resumen", id='btn-vista-resumen',
                              style={'background': '#3b82f6', 'color': 'white', 'padding': '8px 16px', 
                                     'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': '500', 'marginRight': '10px'}),
                    html.Button("🏥 Lesiones", id='btn-vista-lesiones',
                              style={'background': '#ef4444', 'color': 'white', 'padding': '8px 16px', 
                                     'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': '500', 'marginRight': '10px'}),
                    html.Span(f"👤 {usuario['nombre']} - {usuario['club']}", 
                             style={'fontWeight': '500', 'color': '#1e3c72', 'marginRight': '15px'}),
                    html.Button("Cerrar Sesión", id='btn-logout', 
                              style={'background': '#6b7280', 'color': 'white', 'padding': '8px 16px', 
                                     'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': '500'})
                ], className='header-buttons')
            ], className='header-content')
        ], className='app-header'),
        
        # Contenido principal
        html.Div([
            html.Div([
                # Panel izquierdo - Lista de jugadores (Fijo)
                html.Div([
                    html.Div([
                        html.H2("Mi Equipo", style={'color': '#1e3c72', 'margin': 0}),
                        html.Button("➕ Nuevo", id='btn-nuevo-jugador', 
                                  style={'background': '#10b981', 'color': 'white', 'border': 'none', 
                                         'padding': '8px 15px', 'borderRadius': '6px', 'cursor': 'pointer'})
                    ], className='sidebar-header'),
                    
                    html.Div(id='lista-jugadores', style={'overflowY': 'auto', 'height': 'calc(100vh - 200px)'})
                ], className='sidebar', style={'height': 'calc(100vh - 120px)', 'position': 'sticky', 'top': '20px'}),
                
                # Panel derecho - Detalles del jugador (Con scroll)
                html.Div([
                    html.Div(id='ficha-jugador')
                ], className='content', style={'overflowY': 'auto', 'height': 'calc(100vh - 140px)', 'padding': '20px'})
            ], className='dashboard-grid', style={'gridTemplateColumns': '300px 1fr', 'gap': '20px'})
        ], className='main-content'),
        
        # Intervalo para actualización en tiempo real
        dcc.Interval(id='intervalo-simulacion', interval=1000, n_intervals=0, disabled=True)
    ])

def generar_lista_jugadores():
    """Generar lista de jugadores en el sidebar"""
    jugadores = gestor_futbol.obtener_todos_jugadores()
    
    print(f"📋 Generando lista con {len(jugadores)} jugadores")
    
    if not jugadores:
        return html.Div([
            html.Div("👥", style={'fontSize': '3rem', 'textAlign': 'center', 'opacity': 0.5, 'marginBottom': '10px'}),
            html.P("No hay jugadores", style={'textAlign': 'center', 'color': '#666'}),
            html.P("Agrega tu primer jugador", style={'textAlign': 'center', 'color': '#999', 'fontSize': '0.9rem'})
        ])
    
    elementos = []
    for jugador_id, jugador in jugadores.items():
        # Verificar que el jugador tiene los datos necesarios
        if not jugador or 'nombre' not in jugador:
            print(f"⚠️ Jugador {jugador_id} con datos incompletos: {jugador}")
            continue
            
        # Determinar tipo de badge por posición
        pos = jugador.get('posicion', 'Desconocida')
        if 'Portero' in pos:
            badge_class = 'badge-POR'
            badge_text = 'POR'
        elif 'Defensa' in pos:
            badge_class = 'badge-DEF'
            badge_text = 'DEF'
        elif 'Medio' in pos:
            badge_class = 'badge-MED'
            badge_text = 'MED'
        else:
            badge_class = 'badge-DEL'
            badge_text = 'DEL'
        
        # Estado del jugador
        estado_text = 'Lesionado' if jugador.get('lesionado', False) else 'Activo'
        estado_class = 'estado-lesionado' if jugador.get('lesionado', False) else 'estado-activo'
        
        elementos.append(
            html.Div([
                html.Div([
                    html.Span(jugador['nombre'], className='jugador-nombre'),
                    html.Button("✕", 
                        id={'type': 'btn-eliminar', 'index': jugador_id},
                        className='btn-eliminar',
                        n_clicks=0
                    )
                ], style={'position': 'relative'}),
                html.Div([
                    html.Span(f"#{jugador.get('numero', '?')} • {jugador.get('edad', '?')} años • {jugador.get('posicion', '?')}"),
                    html.Br(),
                    html.Span(badge_text, className=f'badge-posicion {badge_class}', 
                            style={'marginTop': '5px', 'display': 'inline-block'}),
                    html.Span(" • ", style={'margin': '0 5px'}),
                    html.Span(estado_text, className=f'estado-badge {estado_class}', 
                            style={'marginTop': '5px', 'display': 'inline-block'})
                ], className='jugador-info'),
            ], 
            className='jugador-card',
            id={'type': 'jugador-card', 'index': jugador_id},
            n_clicks=0,
            style={'position': 'relative'}
            )
        )
    
    if not elementos:
        return html.Div([
            html.P("Error al cargar jugadores", style={'color': '#dc2626', 'textAlign': 'center'})
        ])
    
    return html.Div(elementos)

def generar_ficha_jugador(jugador_id):
    """Generar ficha completa de un jugador"""
    if not jugador_id:
        return generar_vista_equipo()
    
    datos = gestor_futbol.obtener_jugador(jugador_id)
    if not datos:
        return html.Div([
            html.H1("Jugador no encontrado", style={'color': '#dc2626'}),
            html.P("El jugador seleccionado no existe o fue eliminado.", style={'marginTop': '10px'})
        ])
    
    info = datos['info']
    metricas = datos['metricas']
    entrenamientos = datos['entrenamientos']
    medico = datos['medico']
    
    # Estadísticas básicas de entrenamientos
    if entrenamientos:
        distancia_total = sum(e.get('distancia', 0) for e in entrenamientos)
        carga_total = sum(e.get('carga', 0) for e in entrenamientos)
        sprints_total = sum(e.get('sprints', 0) for e in entrenamientos)
        sesiones = len(entrenamientos)
    else:
        distancia_total = carga_total = sprints_total = sesiones = 0
    
    # Preparar datos para gráficos
    if entrenamientos:
        df_entrenamientos = pd.DataFrame(entrenamientos)
        # Gráfico de carga
        fig_carga = px.line(df_entrenamientos, x='fecha', y='carga', 
                           title='📈 Evolución de Carga de Entrenamiento',
                           markers=True)
        fig_carga.update_layout(template='plotly_white', height=300)
        
        # Gráfico de distancia
        fig_distancia = px.bar(df_entrenamientos, x='fecha', y='distancia',
                              title='🏃 Distancia Recorrida por Sesión')
        fig_distancia.update_layout(template='plotly_white', height=300)
    else:
        fig_carga = go.Figure()
        fig_carga.update_layout(title='No hay datos de entrenamiento',
                               template='plotly_white', height=300)
        fig_distancia = go.Figure()
        fig_distancia.update_layout(title='No hay datos de distancia',
                                   template='plotly_white', height=300)
    
    # Badge de posición
    pos = info['posicion']
    if 'Portero' in pos:
        badge_class = 'badge-POR'
        badge_text = 'POR'
    elif 'Defensa' in pos:
        badge_class = 'badge-DEF'
        badge_text = 'DEF'
    elif 'Medio' in pos:
        badge_class = 'badge-MED'
        badge_text = 'MED'
    else:
        badge_class = 'badge-DEL'
        badge_text = 'DEL'
    
    # Obtener datos para mapa de calor
    datos_mapa_calor = metricas.get('mapa_calor_datos', [])
    fig_mapa_calor = crear_campo_futbol_con_mapa_calor(datos_mapa_calor)
    
    return html.Div([
        # Header del jugador
        html.Div([
            html.Div([
                html.H1(info['nombre'], style={'color': '#1e3c72', 'marginBottom': '5px'}),
                html.Div([
                    html.Span(f"#{info['numero']} • ", style={'fontSize': '1.1rem'}),
                    html.Span(info['posicion'], className=f'badge-posicion {badge_class}'),
                    html.Span(f" • 🎂 {info['edad']} años", style={'marginLeft': '10px'}),
                    html.Span(f" • ⚖️ {info['peso']}kg", style={'marginLeft': '10px'}),
                    html.Span(f" • 📏 {info['altura']}cm", style={'marginLeft': '10px'}),
                    html.Span(f" • 👣 {info['pie_habil']}", style={'marginLeft': '10px'})
                ], style={'color': '#666'})
            ]),
            
            html.Div([
                html.Span('Activo' if not info['lesionado'] else 'Lesionado', 
                         className=f'estado-badge {"estado-activo" if not info["lesionado"] else "estado-lesionado"}',
                         style={'padding': '10px 20px', 'fontSize': '1rem'})
            ])
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 
                 'marginBottom': '30px', 'paddingBottom': '20px', 'borderBottom': '2px solid #e5e7eb'}),
        
        # Estadísticas rápidas
        html.Div([
            html.Div([
                html.Div(f"{distancia_total:.1f}", className='stat-valor'),
                html.Div("Km Totales (7d)", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{sesiones}", className='stat-valor'),
                html.Div("Sesiones (7d)", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{sprints_total}", className='stat-valor'),
                html.Div("Sprints Totales", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{carga_total:,}", className='stat-valor'),
                html.Div("Carga Total", className='stat-label')
            ], className='stat-card')
        ], className='stats-grid'),
        
        # Pestañas principales
        dcc.Tabs([
            # Tab 1: Métricas Técnicas
            dcc.Tab(label='🎯 Métricas Técnicas', children=[
                html.Div([
                    html.H3("Habilidades Técnicas", style={'marginBottom': '20px', 'color': '#1e3c72'}),
                    
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span("Definición:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('definicion', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Visión de Juego:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('vision', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Pase:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('pase', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Regate:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('regate', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                        ], style={'flex': 1}),
                        
                        html.Div([
                            html.Div([
                                html.Span("Marcaje:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('marcaje', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Juego Aéreo:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('juego_aereo', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Reflejos:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('reflejos', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Salida de Balón:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('salida_balon', 0)}/100", className='metrica_valor'),
                            ], className='metrica-item'),
                        ], style={'flex': 1})
                    ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}),
                    
                    # Gráfico radial de habilidades
                    html.Div([
                        dcc.Graph(
                            figure=go.Figure(
                                data=go.Scatterpolar(
                                    r=[metricas.get('definicion', 0), metricas.get('vision', 0), 
                                       metricas.get('pase', 0), metricas.get('regate', 0),
                                       metricas.get('marcaje', 0), metricas.get('definicion', 0)],
                                    theta=['Definición', 'Visión', 'Pase', 'Regate', 'Marcaje', 'Definición'],
                                    fill='toself',
                                    fillcolor='rgba(30, 60, 114, 0.3)',
                                    line=dict(color='#1e3c72', width=2)
                                ),
                                layout=go.Layout(
                                    polar=dict(
                                        radialaxis=dict(visible=True, range=[0, 100])
                                    ),
                                    showlegend=False,
                                    height=400
                                )
                            )
                        )
                    ], className='graph-card')
                ], style={'padding': '20px'})
            ]),
            
            # Tab 2: Datos Físicos
            dcc.Tab(label='💪 Datos Físicos', children=[
                html.Div([
                    html.H3("Métricas Físicas", style={'marginBottom': '20px', 'color': '#1e3c72'}),
                    
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span("Velocidad Máxima:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('velocidad_maxima', 0):.1f} km/h", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Aceleración (10m):", className='metrica-nombre'),
                                html.Span(f"{metricas.get('aceleracion_10m', 0):.2f} s", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Salto Vertical:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('salto_vertical', 0):.0f} cm", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("VO₂ Máx:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('vo2_max', 0):.1f} ml/kg/min", className='metrica-valor')
                            ], className='metrica-item'),
                        ], style={'flex': 1}),
                        
                        html.Div([
                            html.Div([
                                html.Span("Frecuencia en Reposo:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('frecuencia_reposo', 0)} lpm", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Frecuencia Máxima:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('frecuencia_maxima', 0)} lpm", className='metrica_valor')
                            ], className='metrica_item'),
                            
                            html.Div([
                                html.Span("Resistencia:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('resistencia', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Recuperación:", className='metrica-nombre'),
                                html.Span(f"{metricas.get('recuperacion', 0)}/100", className='metrica-valor')
                            ], className='metrica-item'),
                        ], style={'flex': 1})
                    ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}),
                    
                    # Gráficos de entrenamiento
                    html.Div([
                        dcc.Graph(figure=fig_carga)
                    ], className='graph-card'),
                    
                    html.Div([
                        dcc.Graph(figure=fig_distancia)
                    ], className='graph-card')
                ], style={'padding': '20px'})
            ]),
            
            # Tab 3: Datos Médicos y Lesiones
            dcc.Tab(label='🏥 Datos Médicos', children=[
                html.Div([
                    html.H3("Información Médica", style={'marginBottom': '20px', 'color': '#1e3c72'}),
                    
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span("Último Control:", className='metrica-nombre'),
                                html.Span(medico.get('ultimo_control', 'N/A'), className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Estado Físico:", className='metrica-nombre'),
                                html.Span(medico.get('estado_fisico', 'N/A'), className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Lesiones Previas:", className='metrica-nombre'),
                                html.Span(str(medico.get('lesiones_previas', 0)), className='metrica-valor')
                            ], className='metrica-item'),
                            
                            html.Div([
                                html.Span("Días Lesionado:", className='metrica-nombre'),
                                html.Span(str(medico.get('dias_lesionado', 0)), className='metrica-valor')
                            ], className='metrica-item'),
                        ], className='metricas-grid'),
                        
                        # Detalles de lesiones con tiempo de baja
                        html.Div([
                            html.H4("📋 Historial de Lesiones", style={'marginTop': '30px', 'marginBottom': '15px', 'color': '#1e3c72'}),
                            html.P("Incluyendo tiempo estimado de baja y estado de recuperación", 
                                  style={'color': '#666', 'marginBottom': '20px'}),
                            
                            html.Div([
                                generar_detalles_lesiones_jugador(medico)
                            ])
                        ]),
                        
                        html.Div([
                            html.H4("Observaciones:", style={'marginTop': '30px', 'marginBottom': '10px'}),
                            html.P(medico.get('observaciones', 'Sin observaciones'), 
                                  style={'padding': '15px', 'background': '#f8fafc', 'borderRadius': '8px'})
                        ])
                    ])
                ], style={'padding': '20px'})
            ]),
            
            # Tab 4: Mapa de Calor (Campo de Fútbol)
            dcc.Tab(label='🔥 Mapa de Calor', children=[
                html.Div([
                    html.H3("Mapa de Calor - Distribución en el Campo", style={'marginBottom': '20px', 'color': '#1e3c72'}),
                    html.P("Intensidad de presencia del jugador en diferentes zonas del campo", 
                          style={'color': '#666', 'marginBottom': '30px'}),
                    
                    # Mapa de calor visual en campo de fútbol
                    html.Div([
                        dcc.Graph(figure=fig_mapa_calor)
                    ], className='graph-card'),
                    
                    # Leyenda del mapa de calor
                    html.Div([
                        html.H4("📊 Interpretación del Mapa:", style={'marginBottom': '10px', 'color': '#1e3c72'}),
                        html.Div([
                            html.Div([
                                html.Span("🔴 Zonas Rojas: ", style={'fontWeight': 'bold', 'color': '#dc2626'}),
                                html.Span("Alta frecuencia - Zonas donde el jugador pasa más tiempo")
                            ], style={'marginBottom': '5px'}),
                            html.Div([
                                html.Span("🟡 Zonas Amarillas: ", style={'fontWeight': 'bold', 'color': '#f59e0b'}),
                                html.Span("Frecuencia media - Zonas de actividad moderada")
                            ], style={'marginBottom': '5px'}),
                            html.Div([
                                html.Span("🟢 Zonas Verdes: ", style={'fontWeight': 'bold', 'color': '#10b981'}),
                                html.Span("Baja frecuencia - Zonas con menor presencia")
                            ])
                        ], style={'padding': '15px', 'background': '#f8fafc', 'borderRadius': '8px'})
                    ])
                ], style={'padding': '20px'})
            ]),
            
            # Tab 5: Simulador de Sensores (NUEVA PESTAÑA)
            dcc.Tab(label='🎮 Simulador Sensores', children=[
                html.Div([
                    html.H3("Simulador de Sensores en Tiempo Real", 
                            style={'marginBottom': '20px', 'color': '#1e3c72'}),
                    
                    # Panel de control de simulación
                    html.Div([
                        html.Div([
                            html.H4("🎮 Control de Simulación", style={'marginBottom': '15px', 'color': '#8b5cf6'}),
                            html.Div([
                                html.Div([
                                    html.Label("Duración (minutos):", 
                                              style={'fontWeight': '500', 'marginRight': '10px'}),
                                    dcc.Input(id='duracion-simulacion', type='number', 
                                             value=90, min=1, max=120, step=1,
                                             style={'width': '80px', 'padding': '8px', 
                                                    'borderRadius': '6px', 'border': '1px solid #ddd'})
                                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),
                                
                                html.Div([
                                    html.Button("▶️ Iniciar Simulación", id='btn-iniciar-simulacion',
                                              className='btn btn-simulacion', 
                                              style={'marginRight': '10px', 'padding': '10px 20px'}),
                                    html.Button("⏹️ Detener", id='btn-detener-simulacion',
                                              className='btn btn-danger', 
                                              style={'marginRight': '10px', 'padding': '10px 20px'}),
                                    html.Button("💾 Guardar Datos", id='btn-guardar-simulacion',
                                              className='btn btn-primary', 
                                              style={'padding': '10px 20px'})
                                ], style={'display': 'flex'}),
                                
                                html.Div(id='estado-simulacion', 
                                        style={'padding': '10px', 'background': '#f8fafc', 
                                               'borderRadius': '8px', 'marginTop': '15px'})
                            ])
                        ], className='panel-simulacion'),
                        
                        # Panel de estadísticas en tiempo real
                        html.Div(id='panel-estadisticas-realtime', 
                                style={'marginTop': '20px'}),
                        
                        # Gráficos en tiempo real
                        html.Div([
                            html.H4("📈 Datos en Tiempo Real", style={'marginBottom': '15px', 'color': '#1e3c72'}),
                            dcc.Graph(id='grafico-tiempo-real'),
                            dcc.Graph(id='grafico-posicion-tiempo-real')
                        ], style={'marginTop': '30px'}),
                        
                        # Almacenamiento de datos
                        dcc.Store(id='store-datos-simulacion')
                        
                    ])
                ], style={'padding': '20px'})
            ]),
            
            # Tab 6: Últimos Entrenamientos
            dcc.Tab(label='📋 Entrenamientos', children=[
                html.Div([
                    html.H3("Historial de Entrenamientos", style={'marginBottom': '20px', 'color': '#1e3c72'}),
                    
                    html.Div([
                        html.Button("➕ Agregar Entrenamiento", id='btn-agregar-entrenamiento',
                                  className='btn btn-primary', style={'marginBottom': '20px'}),
                        
                        html.Div([
                            html.Div([
                                html.Table([
                                    html.Thead(
                                        html.Tr([
                                            html.Th("Fecha"),
                                            html.Th("Tipo"),
                                            html.Th("Duración"),
                                            html.Th("Distancia"),
                                            html.Th("Sprints"),
                                            html.Th("Carga"),
                                            html.Th("Fatiga")
                                        ], style={'backgroundColor': '#1e3c72', 'color': 'white'})
                                    ),
                                    html.Tbody([
                                        html.Tr([
                                            html.Td(e['fecha']),
                                            html.Td(e['tipo']),
                                            html.Td(f"{e['duracion']} min"),
                                            html.Td(f"{e['distancia']} km"),
                                            html.Td(e['sprints']),
                                            html.Td(e['carga']),
                                            html.Td(f"{e['fatiga']}/10")
                                        ]) for e in entrenamientos[-10:]  # Últimos 10 entrenamientos
                                    ])
                                ], style={'width': '100%', 'borderCollapse': 'collapse'})
                            ], style={'overflowX': 'auto'})
                        ])
                    ])
                ], style={'padding': '20px'})
            ])
        ])
    ])

def generar_vista_equipo():
    """Generar vista de estadísticas del equipo"""
    estadisticas = gestor_futbol.calcular_estadisticas_equipo()
    
    elementos = [
        html.H1("🏆 Mi Equipo", style={'color': '#1e3c72', 'marginBottom': '30px'}),
        html.P("Vista general del equipo con estadísticas clave", style={'color': '#666', 'marginBottom': '20px'}),
        
        html.Div([
            html.Div([
                html.Div(f"{estadisticas.get('total_jugadores', 0)}", className='stat-valor'),
                html.Div("Total Jugadores", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('activos', 0)}", className='stat-valor'),
                html.Div("Jugadores Activos", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('lesionados', 0)}", className='stat-valor'),
                html.Div("Jugadores Lesionados", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('edad_promedio', 0)}", className='stat-valor'),
                html.Div("Edad Promedio", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('peso_promedio', 0)}", className='stat-valor'),
                html.Div("Peso Promedio (kg)", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('altura_promedio', 0)}", className='stat-valor'),
                html.Div("Altura Promedio (cm)", className='stat-label')
            ], className='stat-card'),
        ], className='stats-grid'),
        
        html.Div([
            html.H3("📊 Distribución por Posición", style={'marginBottom': '20px', 'color': '#1e3c72'}),
            html.Div(id='grafico-posiciones')
        ], className='graph-card')
    ]
    
    # Mejor jugador del equipo
    mejor = gestor_futbol._obtener_mejor_valorado()
    if mejor:
        elementos.append(html.Div([
            html.H3("⭐ Jugador Mejor Valorado", style={'marginBottom': '20px', 'color': '#1e3c72'}),
            html.Div([
                html.Div([
                    html.H4(mejor['nombre'], style={'color': '#1e3c72', 'marginBottom': '5px'}),
                    html.P(f"#{mejor['numero']} • {mejor['posicion']}"),
                    html.Div([
                        html.Span("Puntuación: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{mejor['puntuacion']}/100", 
                                 style={'color': '#10b981', 'fontSize': '1.2rem', 'fontWeight': 'bold'})
                    ], style={'marginTop': '10px'})
                ], style={'padding': '20px', 'background': '#f8fafc', 'borderRadius': '8px'})
            ])
        ], className='graph-card'))
    
    return html.Div(elementos)

def generar_vista_resumen():
    """Generar vista de resumen del equipo"""
    resumen = gestor_futbol.obtener_resumen_rendimiento()
    estadisticas = resumen.get('estadisticas_generales', {})
    
    elementos = [
        html.H1("📊 Resumen del Equipo", style={'color': '#1e3c72', 'marginBottom': '30px'}),
        
        html.Div([
            html.Div([
                html.Div(f"{resumen.get('puntuacion_promedio_equipo', 0)}", className='stat-valor'),
                html.Div("Puntuación Promedio", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('total_lesiones', 0)}", className='stat-valor'),
                html.Div("Total Lesiones", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('tasa_lesiones_por_jugador', 0):.2f}", className='stat-valor'),
                html.Div("Lesiones por Jugador", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{estadisticas.get('edad_promedio', 0)}", className='stat-valor'),
                html.Div("Edad Promedio", className='stat-label')
            ], className='stat-card'),
        ], className='stats-grid')
    ]
    
    # Mejor jugador
    mejor = gestor_futbol._obtener_mejor_valorado()
    if mejor:
        elementos.append(html.Div([
            html.H3("⭐ Jugador Destacado", style={'marginBottom': '20px', 'color': '#1e3c72'}),
            html.Div([
                html.H4(mejor['nombre'], style={'color': '#1e3c72', 'marginBottom': '5px'}),
                html.P(f"#{mejor['numero']} • {mejor['posicion']} • Puntuación: {mejor['puntuacion']}/100"),
                html.P("Jugador con mejor valoración promedio del equipo", 
                      style={'color': '#666', 'fontSize': '0.9rem', 'marginTop': '10px'})
            ], style={'padding': '20px', 'background': '#f8fafc', 'borderRadius': '8px'})
        ], className='graph-card'))
    
    # Análisis por posición
    elementos.append(html.Div([
        html.H3("👥 Análisis por Posición", style={'marginBottom': '20px', 'color': '#1e3c72'}),
        html.Div(id='analisis-posiciones')
    ], className='graph-card'))
    
    return html.Div(elementos)

def generar_vista_lesiones():
    """Generar vista de análisis de lesiones con tiempo de baja"""
    analisis = gestor_futbol.obtener_analisis_lesiones()
    
    elementos = [
        html.H1("🏥 Análisis de Lesiones", style={'color': '#1e3c72', 'marginBottom': '30px'}),
        html.P("Información detallada sobre lesiones incluyendo tipo y tiempo de baja estimado", 
               style={'color': '#666', 'marginBottom': '20px'}),
        
        html.Div([
            html.Div([
                html.Div(f"{analisis.get('total_lesiones', 0)}", className='stat-valor'),
                html.Div("Total Lesiones", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{analisis.get('tasa_lesiones_por_jugador', 0):.2f}", className='stat-valor'),
                html.Div("Lesiones por Jugador", className='stat-label')
            ], className='stat-card'),
            
            html.Div([
                html.Div(f"{len(analisis.get('jugadores_lesionados_actualmente', []))}", className='stat-valor'),
                html.Div("Lesionados Actual", className='stat-label')
            ], className='stat-card'),
        ], className='stats-grid')
    ]
    
    # Jugadores lesionados actualmente con tiempo de baja
    jugadores_lesionados = analisis.get('jugadores_lesionados_actualmente', [])
    if jugadores_lesionados:
        elementos.append(html.Div([
            html.H3("🤕 Jugadores Lesionados Actualmente", style={'marginBottom': '20px', 'color': '#1e3c72'}),
            html.Div([
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Jugador"),
                            html.Th("Posición"),
                            html.Th("Tipo de Lesión"),
                            html.Th("Tiempo de Baja"),
                            html.Th("Días Transcurridos"),
                            html.Th("Recuperación Estimada")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(f"#{j['numero']} {j['nombre']}"),
                            html.Td(j['posicion']),
                            html.Td(j['tipo_lesion']),
                            html.Td(j['tiempo_baja'], style={'fontWeight': 'bold', 'color': '#dc2626'}),
                            html.Td(f"{j['dias_lesionado']} días"),
                            html.Td(j['recuperacion_estimada'])
                        ]) for j in jugadores_lesionados
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginTop': '20px'})
            ])
        ], className='graph-card'))
    else:
        elementos.append(html.Div([
            html.H3("🤕 Jugadores Lesionados Actualmente", style={'marginBottom': '20px', 'color': '#1e3c72'}),
            html.Div([
                html.Div("✅", style={'fontSize': '3rem', 'textAlign': 'center', 'opacity': 0.5, 'marginBottom': '10px'}),
                html.P("No hay jugadores lesionados actualmente", style={'textAlign': 'center', 'color': '#666'})
            ])
        ], className='graph-card'))
    
    # Gráfico de lesiones por posición
    elementos.append(html.Div([
        html.H3("📊 Lesiones por Posición", style={'marginBottom': '20px', 'color': '#1e3c72'}),
        html.Div(id='grafico-lesiones-posicion')
    ], className='graph-card'))
    
    # Tipos de lesión más comunes con tiempo de baja
    tipos_lesion = analisis.get('tipos_lesion_mas_comunes', {})
    tiempo_baja_por_tipo = analisis.get('tiempo_baja_por_tipo', {})
    
    if tipos_lesion:
        elementos.append(html.Div([
            html.H3("🔍 Tipos de Lesión Más Comunes", style={'marginBottom': '20px', 'color': '#1e3c72'}),
            html.Div([
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Tipo de Lesión"),
                            html.Th("Casos"),
                            html.Th("Tiempo de Baja Promedio")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(tipo),
                            html.Td(f"{cantidad} casos"),
                            html.Td(tiempo_baja_por_tipo.get(tipo, 'N/A'), style={'fontWeight': 'bold', 'color': '#dc2626'})
                        ]) for tipo, cantidad in list(tipos_lesion.items())[:5]
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginTop': '20px'})
            ])
        ], className='graph-card'))
    
    return html.Div(elementos)

# ============================================
# CALLBACKS PRINCIPALES - CORREGIDOS y MEJORADOS
# ============================================

# 1. Controlar qué página mostrar - CORREGIDO
@app.callback(
    Output('pagina-contenido', 'children'),
    Input('usuario-actual', 'data'),
    prevent_initial_call=True
)
def mostrar_pagina(usuario):
    if usuario is None:
        return generar_pagina_login()
    else:
        return generar_pagina_principal(usuario)

# 2. Mostrar contenido inicial - CORREGIDO y MEJORADO
@app.callback(
    Output('ficha-jugador', 'children'),
    [Input('vista-activa', 'data'),
     Input('jugador-seleccionado', 'data')],
    prevent_initial_call=True
)
def mostrar_contenido_inicial(vista_actual, jugador_id):
    ctx = dash.callback_context
    
    # Si es la primera carga
    if not ctx.triggered:
        return generar_vista_equipo()
    
    trigger = ctx.triggered[0]['prop_id']
    
    # Si se cambió la vista activa (equipo, resumen, lesiones)
    if trigger == 'vista-activa.data':
        if vista_actual == 'equipo':
            # En vista "equipo", si hay un jugador seleccionado, mostrar su ficha
            if jugador_id:
                return generar_ficha_jugador(jugador_id)
            else:
                # Si no hay jugador seleccionado, mostrar vista general del equipo
                return generar_vista_equipo()
        elif vista_actual == 'resumen':
            return generar_vista_resumen()
        elif vista_actual == 'lesiones':
            return generar_vista_lesiones()
    
    # Si el trigger fue la selección de un jugador (desde la lista)
    # El trigger será algo como: "{"type":"jugador-card","index":"1"}.n_clicks"
    if 'jugador-card' in trigger:
        if jugador_id:
            return generar_ficha_jugador(jugador_id)
        else:
            return generar_vista_equipo()
    
    # Por defecto, mostrar vista de equipo
    return generar_vista_equipo()

# 3. Login de usuario - CORREGIDO
@app.callback(
    [Output('usuario-actual', 'data'),
     Output('login-alert', 'children')],
    Input('btn-login', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def hacer_login(n_clicks, username, password):
    if n_clicks is None:
        return dash.no_update, ""
    
    if not username or not password:
        return dash.no_update, html.Div("⚠️ Completa todos los campos", className='alert alert-error')
    
    success, usuario = auth_system.verify_login(username, password)
    if success:
        return usuario, ""
    else:
        return dash.no_update, html.Div("❌ Usuario o contraseña incorrectos", className='alert alert-error')

# 4. Registro de usuario - CORREGIDO
@app.callback(
    Output('register-alert', 'children'),
    Input('btn-register', 'n_clicks'),
    [State('register-nombre', 'value'),
     State('register-username', 'value'),
     State('register-email', 'value'),
     State('register-club', 'value'),
     State('register-password', 'value')],
    prevent_initial_call=True
)
def hacer_registro(n_clicks, nombre, username, email, club, password):
    if n_clicks is None:
        return ""
    
    if not all([nombre, username, email, club, password]):
        return html.Div("⚠️ Todos los campos son obligatorios", className='alert alert-error')
    
    if len(password) < 6:
        return html.Div("❌ La contraseña debe tener al menos 6 caracteres", className='alert alert-error')
    
    success, mensaje = auth_system.register_user(username, password, nombre, email, club)
    if success:
        return html.Div("✅ Registro exitoso. Ahora puedes iniciar sesión.", className='alert alert-success')
    else:
        return html.Div(f"❌ {mensaje}", className='alert alert-error')

# 5. Logout - CORREGIDO
@app.callback(
    [Output('usuario-actual', 'data', allow_duplicate=True),
     Output('vista-activa', 'data', allow_duplicate=True),
     Output('jugador-seleccionado', 'data', allow_duplicate=True)],
    Input('btn-logout', 'n_clicks'),
    prevent_initial_call=True
)
def hacer_logout(n_clicks):
    if n_clicks:
        return None, 'equipo', None
    return dash.no_update, dash.no_update, dash.no_update

# 6. Cambiar vista (Equipo, Resumen, Lesiones) - CORREGIDO
@app.callback(
    [Output('vista-activa', 'data'),
     Output('jugador-seleccionado', 'data', allow_duplicate=True)],
    [Input('btn-vista-equipo', 'n_clicks'),
     Input('btn-vista-resumen', 'n_clicks'),
     Input('btn-vista-lesiones', 'n_clicks')],
    prevent_initial_call=True
)
def cambiar_vista(click_equipo, click_resumen, click_lesiones):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'btn-vista-equipo':
        return 'equipo', None
    elif button_id == 'btn-vista-resumen':
        return 'resumen', None
    elif button_id == 'btn-vista-lesiones':
        return 'lesiones', None
    
    return dash.no_update, dash.no_update

# 7. Lista de jugadores - CORREGIDO
@app.callback(
    Output('lista-jugadores', 'children'),
    [Input('usuario-actual', 'data'),
     Input('btn-guardar-jugador', 'n_clicks'),
     Input('btn-confirmar-eliminar', 'n_clicks'),
     Input('btn-guardar-simulacion', 'n_clicks')],
    prevent_initial_call=True
)
def actualizar_lista_jugadores(usuario, guardar_clicks, eliminar_clicks, guardar_simulacion_clicks):
    if not usuario:
        return ""
    
    # Solo actualizar si hay cambios reales
    ctx = dash.callback_context
    if not ctx.triggered:
        return generar_lista_jugadores()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id in ['usuario-actual', 'btn-guardar-jugador', 'btn-confirmar-eliminar', 'btn-guardar-simulacion']:
        return generar_lista_jugadores()
    
    return dash.no_update

# 8. Seleccionar jugador - CORREGIDO
@app.callback(
    [Output('jugador-seleccionado', 'data'),
     Output('vista-activa', 'data', allow_duplicate=True)],
    Input({'type': 'jugador-card', 'index': dash.dependencies.ALL}, 'n_clicks'),
    State({'type': 'jugador-card', 'index': dash.dependencies.ALL}, 'id'),
    prevent_initial_call=True
)
def seleccionar_jugador(clicks, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    # Encontrar qué jugador fue clickeado
    trigger_index = ctx.triggered[0]['index']
    for i, click in enumerate(clicks):
        if click is not None and ids[i]['index'] == trigger_index:
            return ids[i]['index'], 'equipo'
    
    return dash.no_update, dash.no_update

# 9. Gráfico de posiciones - CORREGIDO
@app.callback(
    Output('grafico-posiciones', 'children'),
    [Input('vista-activa', 'data'),
     Input('usuario-actual', 'data')],
    prevent_initial_call=True
)
def actualizar_grafico_posiciones(vista, usuario):
    if vista != 'equipo' or not usuario:
        return ""
    
    estadisticas = gestor_futbol.calcular_estadisticas_equipo()
    distribucion = estadisticas.get('distribucion_posiciones', {})
    
    if not distribucion:
        return html.P("No hay datos de distribución")
    
    fig = px.pie(
        names=list(distribucion.keys()),
        values=list(distribucion.values()),
        title='',
        color_discrete_sequence=px.colors.sequential.Blues
    )
    
    return dcc.Graph(figure=fig)

# 10. Gráfico de lesiones por posición - CORREGIDO
@app.callback(
    Output('grafico-lesiones-posicion', 'children'),
    [Input('vista-activa', 'data'),
     Input('usuario-actual', 'data')],
    prevent_initial_call=True
)
def actualizar_grafico_lesiones_posicion(vista, usuario):
    if vista != 'lesiones' or not usuario:
        return ""
    
    analisis = gestor_futbol.obtener_analisis_lesiones()
    lesiones_posicion = analisis.get('lesiones_por_posicion', {})
    
    if not lesiones_posicion:
        return html.P("No hay datos de lesiones por posición")
    
    fig = px.bar(
        x=list(lesiones_posicion.keys()),
        y=list(lesiones_posicion.values()),
        title='',
        labels={'x': 'Posición', 'y': 'Número de Lesiones'},
        color=list(lesiones_posicion.values()),
        color_continuous_scale='Reds'
    )
    
    return dcc.Graph(figure=fig)

# 11. Análisis por posición en resumen - CORREGIDO
@app.callback(
    Output('analisis-posiciones', 'children'),
    [Input('vista-activa', 'data'),
     Input('usuario-actual', 'data')],
    prevent_initial_call=True
)
def actualizar_analisis_posiciones(vista, usuario):
    if vista != 'resumen' or not usuario:
        return ""
    
    resumen = gestor_futbol.obtener_resumen_rendimiento()
    analisis = resumen.get('analisis_posiciones', {})
    
    if not analisis:
        return html.P("No hay datos de análisis por posición")
    
    elementos = []
    for pos, data in analisis.items():
        elementos.append(html.Div([
            html.H5(pos, style={'color': '#1e3c72', 'marginBottom': '5px'}),
            html.P(f"Jugadores: {data['cantidad']} • Edad Promedio: {data['edad_promedio']}"),
            html.P(f"Activos: {data['estado']['activos']} • Lesionados: {data['estado']['lesionados']}")
        ], style={'padding': '15px', 'background': '#f8fafc', 'borderRadius': '8px', 'marginBottom': '10px'}))
    
    return html.Div(elementos)

# 12. Controlar modal de nuevo jugador - CORREGIDO
@app.callback(
    Output('modal-nuevo-jugador', 'style'),
    [Input('btn-nuevo-jugador', 'n_clicks'),
     Input('btn-cerrar-modal', 'n_clicks'),
     Input('btn-cancelar', 'n_clicks'),
     Input('btn-guardar-jugador', 'n_clicks')],
    prevent_initial_call=True
)
def controlar_modal_nuevo(nuevo_click, cerrar_click, cancelar_click, guardar_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'btn-nuevo-jugador':
        return {'display': 'flex'}
    else:
        return {'display': 'none'}

# 13. Agregar nuevo jugador - CORREGIDO y MEJORADO
@app.callback(
    [Output('modal-nuevo-jugador', 'style', allow_duplicate=True),
     Output('jugador-seleccionado', 'data', allow_duplicate=True),
     Output('vista-activa', 'data', allow_duplicate=True),
     # Añadir estos outputs para limpiar los campos del modal
     Output('input-nombre', 'value'),
     Output('input-numero', 'value'),
     Output('input-edad', 'value'),
     Output('input-peso', 'value'),
     Output('input-altura', 'value')],
    Input('btn-guardar-jugador', 'n_clicks'),
    [State('input-nombre', 'value'),
     State('input-posicion', 'value'),
     State('input-numero', 'value'),
     State('input-edad', 'value'),
     State('input-peso', 'value'),
     State('input-altura', 'value'),
     State('input-pie', 'value')],
    prevent_initial_call=True
)
def agregar_jugador(n_clicks, nombre, posicion, numero, edad, peso, altura, pie):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, '', None, None, None, None
    
    # Verificar campos obligatorios
    campos_obligatorios = [nombre, posicion, edad, peso, altura]
    if any(v is None or (isinstance(v, str) and v.strip() == '') for v in campos_obligatorios):
        print("❌ Faltan campos obligatorios")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        datos = {
            'nombre': nombre.strip(),
            'posicion': posicion,
            'numero': int(numero) if numero else 0,
            'edad': int(edad),
            'peso': float(peso),
            'altura': int(altura),
            'pie_habil': pie or 'Derecho'
        }
        
        print(f"✅ Datos del jugador a agregar: {datos}")
        nuevo_id = gestor_futbol.agregar_jugador(datos)
        
        if nuevo_id:
            print(f"✅ Jugador agregado con ID: {nuevo_id}")
            # Limpiar los campos del modal y cerrarlo
            return {'display': 'none'}, nuevo_id, 'equipo', '', None, None, None, None
        else:
            print("❌ No se pudo agregar el jugador")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
    except Exception as e:
        print(f"❌ Error al agregar jugador: {e}")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# 14. Controlar modal de eliminar jugador - CORREGIDO
@app.callback(
    [Output('modal-eliminar-jugador', 'style'),
     Output('nombre-jugador-eliminar', 'children'),
     Output('store-jugador-eliminar', 'data')],
    [Input({'type': 'btn-eliminar', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('btn-cerrar-modal-eliminar', 'n_clicks'),
     Input('btn-cancelar-eliminar', 'n_clicks')],
    [State({'type': 'btn-eliminar', 'index': dash.dependencies.ALL}, 'id')],
    prevent_initial_call=True
)
def controlar_modal_eliminar(delete_clicks, cerrar_click, cancelar_click, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}, "", None
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Cerrar modal
    if button_id in ['btn-cerrar-modal-eliminar', 'btn-cancelar-eliminar']:
        return {'display': 'none'}, "", None
    
    # Si se hizo clic en un botón de eliminar
    if 'btn-eliminar' in button_id:
        try:
            # Encontrar qué botón fue clickeado
            trigger_index = ctx.triggered[0]['index']
            for i, click in enumerate(delete_clicks):
                if click is not None and ids[i]['index'] == trigger_index:
                    jugador_id = ids[i]['index']
                    jugador = gestor_futbol.obtener_jugador(jugador_id)
                    if jugador:
                        nombre = jugador['info']['nombre']
                        return {'display': 'flex'}, f"Jugador: {nombre}", jugador_id
        except Exception as e:
            print(f"Error al abrir modal de eliminación: {e}")
    
    return {'display': 'none'}, "", None

# 15. Eliminar jugador - CORREGIDO
@app.callback(
    [Output('modal-eliminar-jugador', 'style', allow_duplicate=True),
     Output('jugador-seleccionado', 'data', allow_duplicate=True),
     Output('vista-activa', 'data', allow_duplicate=True)],
    Input('btn-confirmar-eliminar', 'n_clicks'),
    State('store-jugador-eliminar', 'data'),
    prevent_initial_call=True
)
def eliminar_jugador(n_clicks, jugador_id):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update
    
    if not jugador_id:
        print("❌ No hay ID de jugador para eliminar")
        return {'display': 'none'}, None, 'equipo'
    
    try:
        print(f"✅ Eliminando jugador con ID: {jugador_id}")
        if gestor_futbol.eliminar_jugador(jugador_id):
            print(f"✅ Jugador eliminado exitosamente")
            return {'display': 'none'}, None, 'equipo'
        else:
            print("❌ No se pudo eliminar el jugador")
    except Exception as e:
        print(f"❌ Error al eliminar jugador: {e}")
    
    return {'display': 'none'}, None, 'equipo'

# ============================================
# CALLBACKS PARA SIMULADOR DE SENSORES - CORREGIDOS
# ============================================

# 16. Controlar simulación - CORREGIDO
@app.callback(
    [Output('estado-simulacion', 'children'),
     Output('datos-simulacion', 'data'),
     Output('grafico-tiempo-real', 'figure'),
     Output('grafico-posicion-tiempo-real', 'figure'),
     Output('panel-estadisticas-realtime', 'children'),
     Output('intervalo-simulacion', 'disabled')],
    [Input('intervalo-simulacion', 'n_intervals'),
     Input('btn-iniciar-simulacion', 'n_clicks'),
     Input('btn-detener-simulacion', 'n_clicks'),
     Input('btn-guardar-simulacion', 'n_clicks')],
    [State('jugador-seleccionado', 'data'),
     State('duracion-simulacion', 'value'),
     State('datos-simulacion', 'data')],
    prevent_initial_call=True
)
def controlar_simulacion(n_intervals, iniciar_clicks, detener_clicks, guardar_clicks, 
                        jugador_id, duracion, datos_actuales):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Esperando inicio de simulación...", {}, go.Figure(), go.Figure(), "", True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'btn-iniciar-simulacion' and jugador_id:
        if simulador_sensores.iniciar_simulacion(jugador_id, duracion or 90):
            estado = html.Div([
                html.Span("● ", className='indicador-tiempo-real indicador-activo'),
                html.Strong("Simulación en curso"),
                html.P(f"Duración: {duracion or 90} minutos", style={'marginTop': '5px', 'color': '#666'})
            ], className='alert alert-simulacion')
            return estado, {}, go.Figure(), go.Figure(), "", False
        else:
            return "Error al iniciar simulación", {}, go.Figure(), go.Figure(), "", True
    
    elif button_id == 'btn-detener-simulacion' and jugador_id:
        simulador_sensores.detener_simulacion(jugador_id)
        return "Simulación detenida", {}, go.Figure(), go.Figure(), "", True
    
    elif button_id == 'btn-guardar-simulacion' and jugador_id:
        if simulador_sensores.guardar_simulacion(jugador_id, "Simulación guardada"):
            return "✅ Simulación guardada exitosamente", {}, go.Figure(), go.Figure(), "", True
        return "❌ Error guardando simulación", {}, go.Figure(), go.Figure(), "", True
    
    elif button_id == 'intervalo-simulacion' and jugador_id:
        datos = simulador_sensores.obtener_datos_tiempo_real(jugador_id, 30)
        if datos and datos['activo']:
            # Crear gráficos en tiempo real
            fig_tiempo_real = crear_grafico_tiempo_real(datos['datos_recientes'])
            fig_posicion = crear_mapa_calor_tiempo_real(datos['datos_recientes'])
            
            # Crear estadísticas
            estadisticas = html.Div([
                html.H4("📊 Estadísticas Acumuladas", style={'marginBottom': '15px', 'color': '#1e3c72'}),
                html.Div([
                    html.Div([
                        html.Div(f"{datos['metricas_acumuladas']['distancia_total']/1000:.2f}", 
                                style={'fontSize': '1.5rem', 'fontWeight': 'bold', 'color': '#8b5cf6'}),
                        html.Div("Kilómetros", style={'color': '#666'})
                    ], className='simulacion-estadistica'),
                    
                    html.Div([
                        html.Div(f"{datos['metricas_acumuladas']['sprints']}", 
                                style={'fontSize': '1.5rem', 'fontWeight': 'bold', 'color': '#8b5cf6'}),
                        html.Div("Sprints", style={'color': '#666'})
                    ], className='simulacion-estadistica'),
                    
                    html.Div([
                        html.Div(f"{datos['metricas_acumuladas']['contactos_balon']}", 
                                style={'fontSize': '1.5rem', 'fontWeight': 'bold', 'color': '#8b5cf6'}),
                        html.Div("Contactos Balón", style={'color': '#666'})
                    ], className='simulacion-estadistica'),
                    
                    html.Div([
                        html.Div(f"{datos['metricas_acumuladas']['recuperaciones']}", 
                                style={'fontSize': '1.5rem', 'fontWeight': 'bold', 'color': '#8b5cf6'}),
                        html.Div("Recuperaciones", style={'color': '#666'})
                    ], className='simulacion-estadistica'),
                ], className='simulacion-estadisticas'),
                
                html.Div([
                    html.Span("● ", className='indicador-tiempo-real indicador-activo'),
                    html.Span(f"Simulando... Minuto {datos['minuto_actual']:.1f}/{(duracion or 90)}"),
                    html.Span(f" • Velocidad actual: {datos['datos_recientes'][-1]['velocidad'] if datos['datos_recientes'] else 0:.1f} km/h", 
                             style={'marginLeft': '15px'})
                ], style={'marginTop': '15px', 'padding': '10px', 'background': '#f8fafc', 'borderRadius': '8px'})
            ])
            
            estado = html.Div([
                html.Span("● ", className='indicador-tiempo-real indicador-activo'),
                html.Strong("Simulación en curso"),
                html.P(f"Minuto: {datos['minuto_actual']:.1f}/{(duracion or 90)}", style={'marginTop': '5px', 'color': '#666'})
            ], className='alert alert-simulacion')
            
            return estado, datos, fig_tiempo_real, fig_posicion, estadisticas, False
        else:
            return "Simulación no activa", {}, go.Figure(), go.Figure(), "", True
    
    # Estado por defecto
    return "Esperando inicio de simulación...", {}, go.Figure(), go.Figure(), "", True

# 17. Panel de alertas - CORREGIDO
@app.callback(
    Output('panel-alertas', 'children'),
    Input('intervalo-simulacion', 'n_intervals'),
    State('jugador-seleccionado', 'data'),
    prevent_initial_call=True
)
def actualizar_alertas(n_intervals, jugador_id):
    if not jugador_id:
        return ""
    
    datos = simulador_sensores.obtener_datos_tiempo_real(jugador_id, 60)
    if not datos or not datos['datos_recientes']:
        return ""
    
    alertas = []
    ultimo_dato = datos['datos_recientes'][-1]
    
    # Verificar fatiga excesiva
    if ultimo_dato['fatiga'] > 8:
        alertas.append({
            'tipo': 'fatiga',
            'nivel': 'alto',
            'mensaje': f'Fatiga elevada: {ultimo_dato["fatiga"]}/10',
            'recomendacion': 'Considerar sustitución'
        })
    
    # Verificar frecuencia cardíaca
    if ultimo_dato['frecuencia_cardiaca'] > 190:
        alertas.append({
            'tipo': 'frecuencia',
            'nivel': 'medio',
            'mensaje': f'Frecuencia cardíaca muy alta: {ultimo_dato["frecuencia_cardiaca"]} lpm',
            'recomendacion': 'Monitorizar estado del jugador'
        })
    
    # Verificar aceleración muy alta
    if ultimo_dato['aceleracion'] > 4:
        alertas.append({
            'tipo': 'aceleracion',
            'nivel': 'medio',
            'mensaje': f'Aceleración intensa: {ultimo_dato["aceleracion"]:.1f} m/s²',
            'recomendacion': 'Verificar estado físico'
        })
    
    if not alertas:
        return ""
    
    elementos = []
    for alerta in alertas:
        color = '#ef4444' if alerta['nivel'] == 'alto' else \
                '#f59e0b' if alerta['nivel'] == 'medio' else '#3b82f6'
        
        elementos.append(html.Div([
            html.Div([
                html.Strong(f"⚠️ {alerta['tipo'].title()}", style={'color': color}),
                html.P(alerta['mensaje'], style={'margin': '5px 0', 'fontSize': '0.9rem'}),
                html.Small(alerta['recomendacion'], style={'color': '#666', 'fontSize': '0.8rem'})
            ], style={'padding': '10px'})
        ], style={
            'background': 'white',
            'borderLeft': f'4px solid {color}',
            'marginBottom': '10px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }))
    
    return html.Div(elementos)

# ============================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("⚽ FÚTBOL PRO ANALYTICS - SISTEMA COMPLETO CON SIMULADOR")
    print("=" * 60)
    print("Sistema de Gestión y Simulación para Equipos de Fútbol")
    print()
    print("🌐 Accede a la aplicación en: http://127.0.0.1:8050")
    print()
    print("👤 Usuarios de prueba:")
    print("  • entrenador / entrenador123")
    print("  • preparador / preparador123")
    print("=" * 60)
    print()
    print("✅ CARACTERÍSTICAS IMPLEMENTADAS:")
    print("  • ✅ Autenticación de usuarios con deportistas.json")
    print("  • ✅ Gestión completa de jugadores con datos_futbol.json")
    print("  • ✅ Agregar nuevos jugadores (se guardan automáticamente)")
    print("  • ✅ Ver detalles completos de cada jugador")
    print("  • ✅ Eliminar jugadores con confirmación")
    print("  • ✅ Estadísticas del equipo en tiempo real")
    print("  • ✅ Análisis de lesiones con tiempo de baja")
    print("  • ✅ Mapas de calor en campo de fútbol")
    print("  • ✅ 🎮 SIMULADOR DE SENSORES EN TIEMPO REAL")
    print("  • ✅ Métricas simuladas: km recorridos, zonas, aceleración")
    print("  • ✅ Recuperaciones, contactos con balón, fatiga, frecuencia cardíaca")
    print("  • ✅ Gráficos en tiempo real durante simulación")
    print("  • ✅ Sistema de alertas inteligentes")
    print("  • ✅ Guardado automático de simulaciones en JSON")
    print("  • ✅ Todos los datos se guardan automáticamente")
    print("=" * 60)
    print()
    print("🎮 PARA USAR EL SIMULADOR:")
    print("  1. Selecciona un jugador")
    print("  2. Ve a la pestaña 'Simulador Sensores'")
    print("  3. Configura la duración y haz clic en 'Iniciar Simulación'")
    print("  4. Observa los datos en tiempo real")
    print("  5. Usa 'Guardar Datos' para almacenar la simulación")
    print("=" * 60)
    
    app.run(host="127.0.0.1", port=8050, debug=True)
    # Callback de debug para ver el estado de los datos
@app.callback(
    Output('debug-info', 'children'),
    Input('usuario-actual', 'data'),
    prevent_initial_call=True
)
def debug_mostrar_datos(usuario):
    if not usuario:
        return ""
    
    jugadores = gestor_futbol.obtener_todos_jugadores()
    return html.Div([
        html.H4("🔍 Información de Debug"),
        html.P(f"Total jugadores en memoria: {len(jugadores)}"),
        html.P(f"Archivo de datos: {gestor_futbol.data_file}"),
        html.P(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}"),
        html.Pre(json.dumps(list(jugadores.keys()), indent=2) if jugadores else "No hay jugadores")
    ], style={'position': 'fixed', 'bottom': '10px', 'right': '10px', 
              'background': 'white', 'padding': '10px', 'border': '1px solid #ccc',
              'zIndex': '9999', 'fontSize': '12px', 'maxWidth': '300px'})