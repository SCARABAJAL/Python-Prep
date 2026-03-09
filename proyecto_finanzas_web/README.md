# Web cerrada para finanzas personales

Mini proyecto en Flask para llevar tus ingresos/gastos en una aplicación privada (con login).

## Funcionalidades
- Registro con **código de invitación**.
- Inicio de sesión y sesión de usuario.
- Protección básica de formularios con token CSRF.
- Carga de movimientos (ingreso/gasto).
- Resumen de balance total y por categoría.
- Eliminación de movimientos.
- Exportación a CSV para análisis externo.

## Ejecutar en local
```bash
cd proyecto_finanzas_web
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export FLASK_SECRET_KEY="tu-clave-secreta"
export APP_INVITE_CODE="tu-codigo-privado"
export APP_DEBUG="false"
python app.py
```

Luego abre `http://127.0.0.1:5000`.

## ¿Qué hago ahora? (pasos recomendados)
1. Crea tu usuario con el código de invitación.
2. Carga tus gastos e ingresos reales de la última semana.
3. Exporta el CSV y valida categorías repetidas o mal escritas.
4. Define 5-8 categorías fijas para mantener consistencia.
5. Cuando tengas datos de 1 mes, revisa el top de gastos por categoría y ajusta presupuesto.

## Recomendaciones para hacerlo realmente "cerrado"
1. Despliega detrás de VPN o red privada.
2. Usa HTTPS (Nginx + certificado).
3. Configura `FLASK_SECRET_KEY` fuerte y única.
4. Usa una base de datos externa cifrada para producción.
5. Agrega 2FA si lo vas a exponer a Internet.
