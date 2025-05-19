from app import create_app
import os 

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render define PORT automáticamente
    app.run(debug=False, host='0.0.0.0', port=port)
    # app.run(debug=True) # Para desarrollo local
