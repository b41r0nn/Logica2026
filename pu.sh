#!/bin/bash

: <<'EOF'
Este script fue creado para realizar
- git add .
- git commit -m ""
- git push
EOF

# Configura la shell para que salga tan pronto como se encuentre el primer error
set -e

# Agregar cambios en la ruta
git add .

# Pedir al usuario que ingrese el mensaje del commit
echo "Ingresa el mensaje del commit: "
read mensaje

# Realizar el commit con el mensaje proporcionado por el usuario
git commit -m "$mensaje"

# Realizar el push al repositorio remoto
git push origin master BaironCalle

