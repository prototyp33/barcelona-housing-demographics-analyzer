# Solución con cloudflared (Gratis, Sin Tarjeta)

## ¿Por qué cloudflared?

- ✅ **Gratis** - No requiere tarjeta de crédito
- ✅ **TCP nativo** - Funciona directamente con PostgreSQL
- ✅ **Sin límites** - Para uso personal/desarrollo
- ✅ **Fácil de usar** - Similar a ngrok

## Instalación

```bash
brew install cloudflare/cloudflare/cloudflared
```

## Uso

### Opción 1: Script Automático

```bash
./scripts/start_cloudflared_tunnel.sh
```

### Opción 2: Manual

```bash
cloudflared tunnel --url tcp://localhost:5432
```

## Configurar en Looker Studio

Cuando cloudflared inicie, verás algo como:

```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |
|  tcp://xxxx-xx-xx-xx-xx.trycloudflare.com:PORT                                             |
+--------------------------------------------------------------------------------------------+
```

**En Looker Studio - JDBC URL**:
```
jdbc:postgresql://xxxx-xx-xx-xx-xx.trycloudflare.com:PORT/barcelona_housing
```

**O BASIC Connection**:
- **Hostname**: `xxxx-xx-xx-xx-xx.trycloudflare.com` (sin el puerto)
- **Port**: `PORT` (el número que te da cloudflared)
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: (tu contraseña de PostgreSQL)

## Notas Importantes

- ⚠️ La URL cambia cada vez que reinicias cloudflared
- ⚠️ Mantén cloudflared corriendo mientras uses Looker Studio
- ✅ No requiere cuenta ni tarjeta de crédito

## Comparación con ngrok

| Característica | cloudflared | ngrok |
|----------------|-------------|-------|
| Gratis | ✅ | ✅ |
| Requiere tarjeta para TCP | ❌ | ✅ |
| TCP nativo | ✅ | ✅ |
| URL permanente | ❌ | ❌ (gratis) |
| Fácil de usar | ✅ | ✅ |

---

**Para empezar**: Ejecuta `./scripts/start_cloudflared_tunnel.sh`
