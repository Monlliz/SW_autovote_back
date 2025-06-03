from app import create_app  # Importamos la función que crea la app Flask configurada

# Crear instancia de la aplicación usando el factory pattern
app = create_app()

if __name__ == '__main__':
    # Ejecutar la aplicación en modo desarrollo (debug=True para recarga automática y mensajes detallados)
    app.run(debug=True)  # Para desarrollo local
