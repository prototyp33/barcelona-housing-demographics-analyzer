# Configurar ngrok con Autenticación

## Paso 1: Crear Cuenta en ngrok (Gratis)

1. Ve a: https://dashboard.ngrok.com/signup
2. Crea una cuenta (es gratis)
3. Verifica tu email

## Paso 2: Obtener Authtoken

1. Después de login, ve a: https://dashboard.ngrok.com/get-started/your-authtoken
2. Copia tu authtoken (algo como: `2abc123def456ghi789jkl012mno345pqr678stu`)

## Paso 3: Configurar ngrok

Ejecuta en tu terminal:

```bash
~/.ngrok/ngrok config add-authtoken TU_AUTHTOKEN_AQUI
```

Reemplaza `TU_AUTHTOKEN_AQUI` con el token que copiaste.

## Paso 4: Verificar

```bash
~/.ngrok/ngrok version
```

Debería mostrar la versión sin errores.

## Paso 5: Iniciar Túnel

```bash
./scripts/start_ngrok_tunnel.sh
```

Ahora debería funcionar sin errores.

---

**Alternativa Rápida**: Si prefieres no crear cuenta, usa **Heroku Postgres** (ver `docs/QUICK_FIX_LOOKER_STUDIO.md`)
