import pandas as pd
import numpy as np
from scipy.signal import find_peaks


def load_ecg_and_compute_bpm(filepath):
    """
    Carga una señal ECG desde un archivo CSV y calcula la frecuencia cardíaca promedio (BPM).
    El archivo debe tener una columna llamada 'ECG' o la señal numérica en la primera columna.
    """

    # Cargar datos ECG
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise FileNotFoundError(f"No se pudo leer el archivo ECG: {str(e)}")

    # Detectar columna ECG automáticamente
    if "ECG" in df.columns:
        ecg_signal = df["ECG"].values
    else:
        ecg_signal = df.iloc[:, 0].values

    # Si no hay columna de tiempo, generamos una basada en frecuencia de muestreo
    fs = 250  # Frecuencia de muestreo estimada (Hz)
    t = np.arange(len(ecg_signal)) / fs

    # Detectar picos (latidos)
    peaks, _ = find_peaks(ecg_signal, distance=fs/2, height=np.mean(ecg_signal))
    num_beats = len(peaks)

    # Calcular BPM
    duration_sec = len(ecg_signal) / fs
    bpm = (num_beats / duration_sec) * 60 if duration_sec > 0 else 0

    return t, ecg_signal, bpm

