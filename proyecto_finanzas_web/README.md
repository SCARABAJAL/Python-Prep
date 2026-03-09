# Web cerrada para finanzas personales

Mini proyecto en Flask para llevar tus ingresos/gastos en una aplicación privada (con login).

## Funcionalidades
- Registro con **código de invitación**.
- Inicio de sesión y sesión de usuario.
- Carga de movimientos (ingreso/gasto).
- Resumen de balance total y por categoría.
- Eliminación de movimientos.

## Ejecutar en local
```bash
cd proyecto_finanzas_web
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export FLASK_SECRET_KEY="tu-clave-secreta"
export APP_INVITE_CODE="tu-codigo-privado"
python app.py
```

Luego abre `http://127.0.0.1:5000`.

## Recomendaciones para hacerlo realmente "cerrado"
1. Despliega detrás de VPN o red privada.
2. Usa HTTPS (Nginx + certificado).
3. Configura `FLASK_SECRET_KEY` fuerte y única.
4. Usa una base de datos externa cifrada para producción.
5. Agrega 2FA si lo vas a exponer a Internet.
