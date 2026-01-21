# Alternativas a ngrok (Sin Cuenta Necesaria)

Si prefieres no crear cuenta en ngrok, aquí hay alternativas:

## Opción 1: Heroku Postgres (Recomendado)

**Ventajas**:
- ✅ Gratis para desarrollo
- ✅ URL permanente (no cambia)
- ✅ Sin configuración de túnel
- ✅ Funciona desde cualquier lugar

**Desventajas**:
- ⚠️ Requiere actualizar Command Line Tools (ver error anterior)
- ⚠️ Límite de 10K filas en plan gratis

**Pasos**:
1. Actualiza Command Line Tools:
   ```bash
   sudo rm -rf /Library/Developer/CommandLineTools
   sudo xcode-select --install
   ```

2. Instala Heroku:
   ```bash
   brew install heroku/brew/heroku
   ```

3. Sigue: `docs/QUICK_FIX_LOOKER_STUDIO.md`

## Opción 2: cloudflared (Cloudflare Tunnel)

**Ventajas**:
- ✅ Gratis
- ✅ No requiere cuenta para uso básico
- ✅ Más estable que ngrok

**Instalación**:
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Uso**:
```bash
cloudflared tunnel --url tcp://localhost:5432
```

## Opción 3: localtunnel

**Ventajas**:
- ✅ Gratis
- ✅ No requiere cuenta

**Instalación**:
```bash
npm install -g localtunnel
```

**Uso**:
```bash
lt --port 5432
```

**⚠️ Nota**: localtunnel es HTTP, necesitarías un proxy TCP.

## Opción 4: Configurar Port Forwarding en Router

Si tienes acceso a tu router, esta es la solución más permanente:

1. Accede a router (192.168.1.1)
2. Configura port forwarding: 5432 → 192.168.1.75:5432
3. Usa tu IP pública en Looker Studio

Ver: `docs/LOOKER_STUDIO_CONNECTION.md`

## Recomendación

**Para desarrollo rápido**: Configura ngrok (2 minutos, cuenta gratuita)

**Para solución permanente**: Heroku Postgres o Port Forwarding

---

**¿Prefieres configurar ngrok?** Ejecuta:
```bash
./scripts/setup_ngrok_auth.sh
```
