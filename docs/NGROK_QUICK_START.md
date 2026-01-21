# Solución Rápida con ngrok

## Problema

Error con port forwarding de Cursor. Necesitas una solución rápida para conectar Looker Studio.

## Solución: ngrok (2 minutos)

ngrok crea un túnel público a tu PostgreSQL local sin necesidad de configurar router.

### Paso 1: Instalar ngrok

```bash
# Opción A: Usar el script automático
./scripts/quick_ngrok_setup.sh

# Opción B: Manual
brew install ngrok/ngrok/ngrok
```

### Paso 2: Iniciar Túnel

```bash
ngrok tcp 5432
```

Verás algo como:
```
Forwarding  tcp://0.tcp.ngrok.io:12345 -> localhost:5432
```

**Copia la URL**: `0.tcp.ngrok.io:12345`

### Paso 3: Configurar en Looker Studio

**JDBC URL**:
```
jdbc:postgresql://0.tcp.ngrok.io:12345/barcelona_housing
```

**O BASIC Connection**:
- **Hostname**: `0.tcp.ngrok.io`
- **Port**: `12345` (el puerto que te dio ngrok)
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: (tu contraseña de PostgreSQL)

### Paso 4: Mantener ngrok Corriendo

**⚠️ IMPORTANTE**: ngrok debe estar corriendo mientras uses Looker Studio.

Para mantenerlo corriendo en segundo plano:
```bash
# En una terminal separada
ngrok tcp 5432
```

O usar el script:
```bash
./scripts/quick_ngrok_setup.sh
```

## Limitaciones de ngrok

- ❌ La URL cambia cada vez que reinicias ngrok
- ❌ Límite de conexiones en plan gratis
- ✅ Perfecto para desarrollo/pruebas

## Alternativa Permanente: Heroku Postgres

Si necesitas una solución permanente (URL que no cambia):

1. Actualiza Command Line Tools:
   ```bash
   sudo rm -rf /Library/Developer/CommandLineTools
   sudo xcode-select --install
   ```

2. Luego instala Heroku:
   ```bash
   brew install heroku/brew/heroku
   ```

3. Sigue las instrucciones en `docs/QUICK_FIX_LOOKER_STUDIO.md`

---

**Para empezar ahora mismo**: Ejecuta `ngrok tcp 5432` y usa la URL en Looker Studio.
