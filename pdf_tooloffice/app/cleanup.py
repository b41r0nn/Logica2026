import os
import time
import threading
from datetime import datetime, timedelta


def limpiar_uploads(upload_folder):
    """Elimina archivos con más de 7 días en la carpeta uploads."""
    limite = datetime.now() - timedelta(days=7)
    eliminados = 0
    for fname in os.listdir(upload_folder):
        fpath = os.path.join(upload_folder, fname)
        if not os.path.isfile(fpath):
            continue
        mod_time = datetime.fromtimestamp(os.path.getmtime(fpath))
        if mod_time < limite:
            try:
                os.remove(fpath)
                eliminados += 1
            except Exception:
                pass
    if eliminados:
        print(f'[cleanup] {eliminados} archivo(s) eliminado(s) — {datetime.now():%Y-%m-%d %H:%M}')


def _loop(upload_folder):
    """Corre la limpieza cada 24 horas."""
    while True:
        try:
            limpiar_uploads(upload_folder)
        except Exception as e:
            print(f'[cleanup] Error: {e}')
        time.sleep(86400)  # 24 h


def start_cleanup_scheduler(upload_folder, *_):
    """Arranca el hilo de limpieza como daemon (muere con la app)."""
    t = threading.Thread(target=_loop, args=(upload_folder,), daemon=True)
    t.start()
