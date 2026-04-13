"""
routes.py — Endpoints Flask
Cada endpoint recibe archivos via multipart/form-data,
llama a services.py, registra en SQLite y retorna el archivo procesado.
"""

import io
import os
import uuid

from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from .database import registrar_log
from .services import (
	cifrar_pdf,
	comprimir_pdf,
	contar_paginas,
	dividir_pdf,
	dividir_pdf_por_modo,
	docx_a_pdf,
	pdf_a_docx,
	pdf_a_xlsx,
	unir_pdfs,
	xlsx_a_pdf,
)

bp = Blueprint('main', __name__)

ALLOWED_PDF  = {'pdf'}
ALLOWED_CONV = {'pdf', 'xlsx', 'docx'}


# ── Helpers ───────────────────────────────────────────────────────

def extension(filename):
	return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def guardar_temporal(file_obj, upload_folder):
	"""Guarda un FileStorage en disco con nombre único. Retorna la ruta."""
	nombre_seguro = secure_filename(file_obj.filename)
	nombre_unico  = f"{uuid.uuid4().hex}_{nombre_seguro}"
	ruta = os.path.join(upload_folder, nombre_unico)
	file_obj.save(ruta)
	return ruta, nombre_seguro


def eliminar_temporales(*rutas):
	for ruta in rutas:
		try:
			if ruta and os.path.isfile(ruta):
				os.remove(ruta)
		except Exception:
			pass


def log_y_enviar(db_path, modulo, nombre, tamano, resultado_bytes,
				 nombre_salida, mimetype, detalle=None):
	"""Registra el log y retorna el archivo al cliente."""
	registrar_log(db_path, modulo, nombre, tamano, 'exito', detalle)
	return send_file(
		io.BytesIO(resultado_bytes),
		mimetype=mimetype,
		as_attachment=True,
		download_name=nombre_salida
	)


def error_response(db_path, modulo, nombre, tamano, msg):
	registrar_log(db_path, modulo, nombre, tamano, 'error', msg)
	return jsonify({'error': msg}), 400


# ── Página principal ──────────────────────────────────────────────

@bp.route('/')
def index():
	return render_template('index.html')


# ── Páginas de archivos ───────────────────────────────────────────

@bp.route('/api/paginas', methods=['POST'])
def paginas():
	"""Retorna el número de páginas de un PDF."""
	upload_folder = current_app.config['UPLOAD_FOLDER']
	f = request.files.get('archivo')
	if not f or extension(f.filename) != 'pdf':
		return jsonify({'error': 'Se requiere un archivo PDF'}), 400

	ruta = None
	try:
		ruta, _ = guardar_temporal(f, upload_folder)
		total = contar_paginas(ruta)
		return jsonify({'paginas': total})
	except Exception as e:
		return jsonify({'error': str(e)}), 500
	finally:
		eliminar_temporales(ruta)


# ── Unión ─────────────────────────────────────────────────────────

@bp.route('/api/union', methods=['POST'])
def union():
	upload_folder = current_app.config['UPLOAD_FOLDER']
	db_path       = current_app.config['DATABASE_PATH']
	archivos = request.files.getlist('archivos')
	contrasena = request.form.get('contrasena_union', '')

	if len(archivos) < 2:
		return jsonify({'error': 'Se necesitan al menos 2 archivos PDF'}), 400

	rutas  = []
	nombre = 'union_multiple.pdf'
	tamano = 0

	try:
		for f in archivos:
			if extension(f.filename) != 'pdf':
				return jsonify({'error': f'"{f.filename}" no es un PDF'}), 400
			ruta, _ = guardar_temporal(f, upload_folder)
			rutas.append(ruta)
			tamano += os.path.getsize(ruta)

		nombre_salida = request.form.get('nombre_salida', 'documento_unido.pdf')
		resultado = unir_pdfs(rutas, contrasena=contrasena)
		return log_y_enviar(db_path, 'union', nombre, tamano,
							resultado, nombre_salida, 'application/pdf')
	except Exception as e:
		return error_response(db_path, 'union', nombre, tamano, str(e))
	finally:
		eliminar_temporales(*rutas)


# ── División ──────────────────────────────────────────────────────

@bp.route('/api/division', methods=['POST'])
def division():
	upload_folder = current_app.config['UPLOAD_FOLDER']
	db_path       = current_app.config['DATABASE_PATH']
	f = request.files.get('archivo')

	if not f or extension(f.filename) != 'pdf':
		return jsonify({'error': 'Se requiere un archivo PDF'}), 400

	ruta, nombre = guardar_temporal(f, upload_folder)
	tamano = os.path.getsize(ruta)

	try:
		modo = request.form.get('modo', 'rango')
		if modo == 'rango':
			inicio = int(request.form.get('inicio', 1))
			fin    = int(request.form.get('fin', 1))
			resultado = dividir_pdf(ruta, inicio, fin)
			nombre_salida = f'paginas_{inicio}_a_{fin}.pdf'
			mimetype = 'application/pdf'
			detalle = f'modo=rango; paginas {inicio}-{fin}'
		else:
			resultado, tipo = dividir_pdf_por_modo(ruta, modo)
			if tipo == 'zip':
				nombre_salida = 'division_todas.zip'
				mimetype = 'application/zip'
			else:
				nombre_salida = f'division_{modo}.pdf'
				mimetype = 'application/pdf'
			detalle = f'modo={modo}'

		return log_y_enviar(db_path, 'division', nombre, tamano,
							resultado, nombre_salida, mimetype,
							detalle=detalle)
	except ValueError as e:
		return error_response(db_path, 'division', nombre, tamano, str(e))
	except Exception as e:
		return error_response(db_path, 'division', nombre, tamano, str(e))
	finally:
		eliminar_temporales(ruta)


# ── Conversión ────────────────────────────────────────────────────

_MIMETYPES = {
	'pdf':  'application/pdf',
	'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

@bp.route('/api/conversion', methods=['POST'])
def conversion():
	upload_folder = current_app.config['UPLOAD_FOLDER']
	db_path       = current_app.config['DATABASE_PATH']
	f = request.files.get('archivo')
	direccion = request.form.get('direccion', '')

	if not f:
		return jsonify({'error': 'Se requiere un archivo'}), 400

	ext_entrada = extension(f.filename)
	if ext_entrada not in ALLOWED_CONV:
		return jsonify({'error': 'Formato no permitido'}), 400

	ruta, nombre = guardar_temporal(f, upload_folder)
	tamano = os.path.getsize(ruta)

	try:
		if direccion == 'pdf-docx':
			resultado   = pdf_a_docx(ruta)
			ext_salida  = 'docx'
		elif direccion == 'pdf-xlsx':
			resultado   = pdf_a_xlsx(ruta)
			ext_salida  = 'xlsx'
		elif direccion == 'docx-pdf':
			resultado   = docx_a_pdf(ruta)
			ext_salida  = 'pdf'
		elif direccion == 'xlsx-pdf':
			resultado   = xlsx_a_pdf(ruta)
			ext_salida  = 'pdf'
		else:
			return jsonify({'error': f'Dirección desconocida: {direccion}'}), 400

		nombre_salida = nombre.rsplit('.', 1)[0] + '_convertido.' + ext_salida
		return log_y_enviar(db_path, 'conversion', nombre, tamano,
							resultado, nombre_salida, _MIMETYPES[ext_salida],
							detalle=direccion)
	except Exception as e:
		return error_response(db_path, 'conversion', nombre, tamano, str(e))
	finally:
		eliminar_temporales(ruta)


# ── Compresión ────────────────────────────────────────────────────

@bp.route('/api/compresion', methods=['POST'])
def compresion():
	upload_folder = current_app.config['UPLOAD_FOLDER']
	db_path       = current_app.config['DATABASE_PATH']
	f = request.files.get('archivo')

	if not f or extension(f.filename) != 'pdf':
		return jsonify({'error': 'Se requiere un archivo PDF'}), 400

	ruta, nombre = guardar_temporal(f, upload_folder)
	tamano = os.path.getsize(ruta)

	try:
		nivel     = request.form.get('nivel', 'media')
		resultado = comprimir_pdf(ruta, nivel)
		nombre_salida = nombre.rsplit('.', 1)[0] + '_comprimido.pdf'
		return log_y_enviar(db_path, 'compresion', nombre, tamano,
							resultado, nombre_salida, 'application/pdf',
							detalle=f'nivel={nivel}')
	except Exception as e:
		return error_response(db_path, 'compresion', nombre, tamano, str(e))
	finally:
		eliminar_temporales(ruta)


# ── Cifrado ───────────────────────────────────────────────────────

@bp.route('/api/cifrado', methods=['POST'])
def cifrado():
	upload_folder = current_app.config['UPLOAD_FOLDER']
	db_path       = current_app.config['DATABASE_PATH']
	f = request.files.get('archivo')

	if not f or extension(f.filename) != 'pdf':
		return jsonify({'error': 'Se requiere un archivo PDF'}), 400

	ruta, nombre = guardar_temporal(f, upload_folder)
	tamano = os.path.getsize(ruta)

	try:
		contrasena = request.form.get('contrasena', '')
		confirmar  = request.form.get('confirmar', '')

		if not contrasena:
			return jsonify({'error': 'La contraseña no puede estar vacía'}), 400
		if contrasena != confirmar:
			return jsonify({'error': 'Las contraseñas no coinciden'}), 400

		resultado = cifrar_pdf(ruta, contrasena)
		nombre_salida = nombre.rsplit('.', 1)[0] + '_cifrado.pdf'
		return log_y_enviar(db_path, 'cifrado', nombre, tamano,
							resultado, nombre_salida, 'application/pdf')
	except Exception as e:
		return error_response(db_path, 'cifrado', nombre, tamano, str(e))
	finally:
		eliminar_temporales(ruta)


# ── Logs (solo acceso interno desde el servidor) ──────────────────

@bp.route('/admin/logs')
def ver_logs():
	"""Vista de logs — accesible solo desde la red local."""
	from .database import obtener_logs
	db_path = current_app.config['DATABASE_PATH']
	logs = obtener_logs(db_path, limit=500)

	# Construye tabla HTML simple
	filas = ''.join(
		f"<tr><td>{r['id']}</td><td>{r['fecha']}</td><td>{r['hora']}</td>"
		f"<td>{r['modulo']}</td><td>{r['archivo']}</td>"
		f"<td>{r['tamano_kb']} KB</td><td>{r['resultado']}</td>"
		f"<td>{r['detalle'] or ''}</td></tr>"
		for r in logs
	)
	html = f"""<!DOCTYPE html><html><head><meta charset=\"UTF-8\"> 
	<title>Logs — PDF ToolOffice</title>
	<style>
	  body{{font-family:sans-serif;padding:24px;background:#f5f7fc}}
	  h2{{color:#0f1e3d;margin-bottom:16px}}
	  table{{border-collapse:collapse;width:100%;font-size:13px}}
	  th{{background:#1b4fd8;color:white;padding:8px 12px;text-align:left}}
	  td{{padding:7px 12px;border-bottom:1px solid #dde6f5}}
	  tr:nth-child(even){{background:#ebf2ff}}
	  .ok{{color:#16a34a;font-weight:600}}
	  .err{{color:#dc2626;font-weight:600}}
	</style></head><body>
	<h2>Registro de operaciones — PDF ToolOffice</h2>
	<p style="color:#4b5680;margin-bottom:16px">Últimas 500 operaciones · acceso solo interno</p>
	<table>
	  <thead><tr>
		<th>#</th><th>Fecha</th><th>Hora</th><th>Módulo</th>
		<th>Archivo</th><th>Tamaño</th><th>Resultado</th><th>Detalle</th>
	  </tr></thead>
	  <tbody>{filas}</tbody>
	</table>
	</body></html>"""
	return html