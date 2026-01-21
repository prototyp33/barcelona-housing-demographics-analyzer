# Problema: cloudflared TCP no funciona con Looker Studio

## Problema Identificado

Cloudflared con "quick tunnels" (sin cuenta) tiene limitaciones con TCP directo. Muestra una URL HTTPS pero PostgreSQL necesita TCP puro.

## Solución: Usar Heroku Postgres (Recomendado)

La mejor solución es migrar a Heroku Postgres, que:
- ✅ Funciona directamente con Looker Studio
- ✅ No requiere túnel
- ✅ URL permanente
- ✅ Gratis para desarrollo

### Pasos Rápidos

1. **Actualizar Command Line Tools** (si es necesario):
   ```bash
   sudo rm -rf /Library/Developer/CommandLineTools
   sudo xcode-select --install
   ```

2. **Instalar Heroku**:
   ```bash
   brew install heroku/brew/heroku
   ```

3. **Login y crear base de datos**:
   ```bash
   heroku login
   heroku create barcelona-housing
   heroku addons:create heroku-postgresql:mini
   ```

4. **Migrar datos**:
   ```bash
   heroku pg:push barcelona_housing DATABASE_URL
   ```

5. **Obtener credenciales**:
   ```bash
   heroku pg:credentials:url
   ```

6. **Usar en Looker Studio** con las credenciales de Heroku

## Alternativa: Configurar Port Forwarding en Router

Si tienes acceso a tu router:

1. Accede a router (192.168.1.1)
2. Configura port forwarding: 5432 → 192.168.1.75:5432
3. Usa tu IP pública en Looker Studio: `37.133.54.161:5432`

Ver: `docs/LOOKER_STUDIO_CONNECTION.md`

## Por qué cloudflared no funciona bien para TCP

- Quick tunnels están diseñados para HTTP/HTTPS
- TCP requiere configuración adicional o cuenta de Cloudflare
- Los puertos TCP no se exponen directamente en quick tunnels

---

**Recomendación**: Usa Heroku Postgres para una solución permanente y confiable.
