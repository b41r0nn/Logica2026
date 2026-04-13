# Sistema de alertas de medicamentos vía correo

Script Python que lee un archivo CSV con medicamentos y sus horas de toma,
y envía un correo electrónico de alerta en el minuto exacto programado.

---

## Estructura del proyecto

```
proyecto_medicamentos/
├── .env                  ← credenciales (no subir a repositorios)
├── .env.example          ← plantilla de configuración
├── medicamento.py        ← clase de dominio Medicamento
├── cargador_csv.py       ← clase CargadorCSV (lee con pandas)
├── notificador.py        ← clase NotificadorCorreo (envío SMTP)
├── main.py               ← MonitorMedicamentos + punto de entrada
├── medicamentos.csv      ← lista de medicamentos y horas
└── requirements.txt      ← dependencias Python
```

---

## Requisitos previos

- Python 3.9 o superior
- Una cuenta de Gmail con **contraseña de aplicación** habilitada  
  *(Cuenta de Google → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones)*

---

## Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt
```

---

## Configuración

1. Copia `.env.example` a `.env`:

   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # macOS / Linux
   ```

2. Edita `.env` con tus datos reales:

   ```dotenv
   MAIL_USERNAME=tu_correo@gmail.com
   MAIL_PASSWORD=abcd efgh ijkl mnop   # contraseña de aplicación de 16 caracteres
   MAIL_ALERT=destinatario@example.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

   > Para enviar a varios destinatarios, sepáralos con coma:
   > `MAIL_ALERT=uno@example.com,dos@example.com`

---

## Editar los medicamentos

Modifica `medicamentos.csv` con tus propios medicamentos y horarios (formato `HH:MM`, 24 h):

```csv
medicamento,hora
Paracetamol,08:00
Ibuprofeno,14:30
Vitamina C,22:00
```

> El CSV se recarga automáticamente cada día a la medianoche,
> por lo que puedes editarlo sin reiniciar el script.

---

## Ejecución

```bash
# Desde la carpeta proyecto_medicamentos (con el entorno virtual activo)
python main.py
```

Salida esperada:

```
=======================================================
  Sistema de alertas de medicamentos vía correo
=======================================================
✅ 3 medicamento(s) cargado(s) desde 'medicamentos.csv'.
🟢 Monitor iniciado — revisando cada 60 segundo(s).
   Medicamentos cargados: ['Paracetamol', 'Ibuprofeno', 'Vitamina C']
   Presiona Ctrl+C para detener.

⏰ [08:00] Hora de tomar Paracetamol
📧 Correo enviado a ['destinatario@example.com'] — Medicamento: Paracetamol (08:00)
```

Detener el script:

```
Ctrl+C
```

---

## Diseño (clases)

| Clase | Archivo | Responsabilidad |
|---|---|---|
| `Medicamento` | `medicamento.py` | Modelo de datos: nombre + hora |
| `CargadorCSV` | `cargador_csv.py` | Lee el CSV con pandas y retorna objetos `Medicamento` |
| `NotificadorCorreo` | `notificador.py` | Construye y envía correos SMTP con TLS |
| `MonitorMedicamentos` | `main.py` | Bucle principal de revisión y orquestación |

---

## Criterios de aceptación cumplidos

- ✅ Envía correo en el minuto exacto de cada medicamento.
- ✅ No reenvía en el mismo minuto (el bucle duerme 60 s entre revisiones).
- ✅ Errores SMTP no detienen el script (solo se muestran en consola).
- ✅ Se detiene limpiamente con `Ctrl+C`.
- ✅ Recarga automática del CSV cada medianoche.

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Error de autenticación SMTP` | Contraseña incorrecta | Genera una nueva contraseña de aplicación en Google |
| `No se encontró el archivo CSV` | Ruta incorrecta | Ejecuta el script desde la carpeta `proyecto_medicamentos/` |
| `Faltan variables en .env` | `.env` no configurado | Copia `.env.example` a `.env` y complétalo |
| No llegan correos | Filtro de spam | Revisa la carpeta de spam del destinatario |
