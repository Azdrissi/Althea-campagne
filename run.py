#!/usr/bin/env python3
import os
import sys
import webbrowser
import socket
from threading import Timer

def open_browser():
    """Ouvre le navigateur (une seule fois) après 1.5 secondes"""
    # Éviter l'ouverture multiple avec le reloader de Flask
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return
    webbrowser.open('http://localhost:5001')

def main():
    # Importer l'application
    from app import create_app

    # Créer l'application
    app = create_app()

    # Obtenir l'adresse IP locale
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("\n" + "="*70)
    print("🚀 APPLICATION FONDATION ALTHEA")
    print("="*70)
    print(f"\n📍 Accès PC:        http://localhost:5001")
    print(f"📱 Accès Mobile:    http://{local_ip}:5001/mobile")
    print("\n💡 Pour arrêter: Ctrl+C")
    print("="*70 + "\n")

    # Ouvrir le navigateur automatiquement après 1.5 secondes
    Timer(1.5, open_browser).start()

    # Lancer le serveur
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application arrêtée")
        sys.exit(0)
