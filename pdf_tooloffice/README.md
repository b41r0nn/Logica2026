# PDF ToolOffice

Este documento describe el estado actual de `pdf_tooloffice`, incluyendo frontend y backend, su arquitectura y la forma recomendada de ejecucion en WSL.

## Guia rapida (WSL)

1. Entrar al proyecto y activar entorno:

```bash
cd /home/b41r0n/Logica2026-1/pdf_tooloffice
source .venv_wsl/bin/activate
```

2. Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Levantar servidor:

```bash
python run.py
```

4. Prueba de humo (esperado: 200 en `/` y 400 controlados en endpoints sin archivo):

```bash
python -c "import sys; sys.path.insert(0,'/home/b41r0n/Logica2026-1/pdf_tooloffice'); from app import create_app; app=create_app(); c=app.test_client(); print('INDEX', c.get('/').status_code); print('PAGINAS', c.post('/api/paginas').status_code); print('UNION', c.post('/api/union').status_code); print('CONVERSION', c.post('/api/conversion').status_code)"
```

## 1. Estado del proyecto

- El proyecto tiene una interfaz frontend funcional en navegador (HTML + CSS + JS).
- El backend Flask esta implementado con endpoints para union, division, conversion, compresion y cifrado.
- El frontend esta conectado con `fetch` al backend para ejecutar operaciones reales y descargar resultados.
- La validacion base front-back esta correcta (render de `/` y respuestas API esperadas para requests incompletos).

Archivos clave de frontend:

- `app/app/templates/index.html`: estructura completa de la interfaz.
- `app/app/static/css/style.css`: estilos, layout, responsive, estados visuales.
- `app/app/static/js/main.js`: navegacion por pestañas, carga de archivos, validacion de tamaño, progreso, requests y descarga.
- `mapa_procesos_front_pdf_tooloffice.svg`: diagrama del flujo principal del frontend.

Archivos clave de backend:

- `app/app/__init__.py`: creacion y configuracion de la app Flask.
- `app/app/routes.py`: endpoints HTTP.
- `app/app/services.py`: logica de procesamiento PDF.
- `app/app/database.py`: registro y consulta de logs en SQLite.
- `app/app/cleanup.py`: limpieza programada de archivos en uploads.
- `app/requirements.txt` y `requirements.txt`: dependencias Python.

## 2. Arquitectura backend

El backend esta implementado en Flask y se organiza por capas:

1. `routes.py`: valida requests, extrae parametros y responde HTTP.
2. `services.py`: ejecuta operaciones de negocio sobre PDF/docx/xlsx.
3. `database.py`: persiste logs de operaciones en SQLite.
4. `cleanup.py`: elimina archivos temporales antiguos.

Nota de conversion PDF -> Excel:

- El backend usa un extractor especializado de tablas (`pdfplumber`) cuando esta disponible.
- Si el PDF no permite extraer tablas con ese metodo, aplica fallback automatico con PyMuPDF y heuristicas por coordenadas.

### Endpoints disponibles

- `GET /`: interfaz web.
- `POST /api/paginas`: cuenta paginas de un PDF.
- `POST /api/union`: une multiples PDFs.
- `POST /api/division`: extrae rango de paginas.
- `POST /api/conversion`: convierte entre PDF, DOCX y XLSX.
- `POST /api/compresion`: comprime PDF por nivel.
- `POST /api/cifrado`: protege PDF con contraseña.
- `GET /admin/logs`: vista HTML de logs.

### Logs

Se guarda por cada operacion:

- fecha y hora
- modulo
- nombre de archivo
- tamaño en KB
- resultado (exito/error)
- detalle adicional

## 3. Ejecucion recomendada en WSL

Usar entorno virtual Linux dentro del proyecto (ejemplo ya creado: `.venv_wsl`):

```bash
cd /home/b41r0n/Logica2026-1/pdf_tooloffice
source .venv_wsl/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Nota importante:

- Si trabajas en terminal WSL, evita usar el entorno virtual tipo Windows (`.venv/Scripts/python.exe`) porque puede generar errores de formato o mezcla de entornos.

## 4. Modulos del frontend (pestañas)

La barra superior muestra 5 módulos:

1. Unión
2. División
3. Conversión
4. Compresión
5. Cifrado

Cada modulo se representa como un panel (`section.panel`) y solo uno esta activo a la vez.

## 5. Flujo del usuario (implementado hoy)

### Paso 1. Seleccion de herramienta

El usuario selecciona una pestaña del menú superior. El JS:

- quita la clase `active` de todas las pestañas/paneles,
- activa la pestaña clicada,
- muestra el panel correspondiente por `data-panel`.

### Paso 2. Carga de archivo(s)

Cada panel tiene una zona de carga (`.upload-zone`) con dos mecanismos:

- Drag & drop
- Clic en input file

En Unión se permite `multiple`; en el resto, carga simple.

### Paso 3. Validacion automatica de tamaño

`main.js` define:

- `MAX_MB = 50`
- `MAX_BYTES = 50 * 1024 * 1024`

Si un archivo excede el límite:

- no se agrega a la lista,
- se muestra toast: `"<nombre>" supera el límite de 50 MB`.

### Paso 4. Configuracion por modulo

Cada pestaña ofrece controles distintos:

- Union: nombre del archivo final.
- Division: modo (rango/todas/pares/impares) + pagina inicio/fin.
- Conversion: direccion de conversion (PDF<->Word/Excel).
- Compresion: nivel (baja/media/alta).
- Cifrado: contraseña + confirmacion.

### Paso 5. Ejecucion

Al pulsar `.btn-process`:

- si no hay archivos, se muestra toast: `Primero sube un archivo PDF`.
- si hay archivo(s):
  - se deshabilita el botón (`btn.disabled = true`),
  - se muestra `.progress-wrap`,
  - se envía `FormData` al endpoint correspondiente,
  - se muestra progreso visual durante la espera de la respuesta.

### Paso 6. Finalizacion

Cuando llega la respuesta del backend:

- se oculta la barra,
- se muestra `.result-box` con botón Descargar,
- se reactiva el botón principal,
- aparece toast de éxito y se dispara descarga automática del archivo generado.



Coincidencias directas:

1. Selección por pestañas: **sí implementado**.
2. Carga por arrastrar/soltar o clic: **sí implementado**.
3. Validación 50MB: **sí implementado** en JS.
4. Configuración según herramienta: **sí implementado** en HTML.
5. Ejecucion con boton bloqueado + progreso: si implementado.
6. Resultado con descarga al 100%: si implementado.

Matiz importante: el progreso mostrado es visual, pero la operacion del archivo si se ejecuta en backend.

## 6. Estado de validacion actual

Validacion realizada:

1. Imports de dependencias del backend: OK.
2. Creacion de app Flask: OK.
3. Render de `GET /`: OK (200).
4. Respuestas base esperadas en endpoints sin payload valido: OK (400 con mensajes coherentes).

Pendientes funcionales recomendados:

1. Completar en backend los modos avanzados de division (`todas`, `pares`, `impares`).
2. Fortalecer validacion de tipo de archivo segun direccion de conversion.
3. Agregar autenticacion para `/admin/logs`.

## 7. Respuestas a preguntas de interfaz

### 7.1 ¿Como se ingresan los rangos en Division?

Actualmente se ingresan con **inputs numéricos**:

- `Página inicio` (`input type="number"`)
- `Página fin` (`input type="number"`)

Además, existe un selector de modo por radios tipo píldora:

- Por rango
- Todas las páginas
- Solo pares
- Solo impares

No hay selección visual de miniaturas/páginas todavía.

### 7.2 En Conversion, ¿como se elige Word o Excel?

Se selecciona mediante **opciones de radio tipo píldora** en “Dirección de conversión”:

- PDF → Excel
- PDF → Word
- Excel → PDF
- Word → PDF

Es una selección explícita de dirección, no un selector dropdown.

### 7.3 ¿Hay boton para eliminar archivo cargado?

Sí. Cada archivo agregado a `.file-list` incluye un botón `.file-remove` (ícono X) que elimina el ítem de la lista en el frontend.

## 8. Comportamientos UI/UX relevantes

- Header sticky con logo, tabs y versión.
- Zonas de carga con estado visual `dragover`.
- Lista de archivos con nombre, tamaño formateado y acción quitar.
- Vista previa en División (nombre + placeholder de páginas).
- Toast global para errores/éxitos.
- Diseño responsive básico para móvil (`@media max-width: 600px`).

## 9. Limitaciones actuales

- No hay validacion profunda de tipo MIME (solo `accept` del input y flujo visual).
- Falta completar algunos modos avanzados en división (todas/pares/impares) en backend.
- El texto de validacion sin archivos menciona PDF incluso en conversion (detalle de UX a ajustar).

## 10. Integracion pendiente

Mejoras recomendadas para robustecer producción:

1. Añadir progreso real por etapas (si se requiere UX mas precisa).
2. Implementar validacion estricta de extension/tipo por direccion de conversion.
3. Completar división por modos `todas`, `pares` e `impares`.
4. Añadir autenticacion para vista de logs de administracion.

## 11. Resumen rapido

El sistema ya cubre el flujo completo (seleccion -> carga -> validacion -> configuracion -> ejecucion en backend -> descarga del resultado), con interfaz consistente y backend funcional. Lo pendiente esta en validaciones avanzadas, seguridad y algunos modos de operacion.

## 12. Logs

La base de datos de logs conserva registro del nombre del archivo, tamaño, fecha, hora, modulo y resultado de la operacion.