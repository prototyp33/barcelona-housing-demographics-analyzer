# Solución Final: Conectar Looker Studio a PostgreSQL

## Problema

Cloudflared quick tunnels no exponen TCP directamente para PostgreSQL. Looker Studio necesita una conexión TCP directa.

## Solución Recomendada: Heroku Postgres

### ¿Por qué Heroku?
- ✅ **Gratis** para desarrollo
- ✅ **Funciona directamente** con Looker Studio (sin túnel)
- ✅ **URL permanente** (no cambia)
- ✅ **Sin configuración** de router/firewall
- ✅ **Fácil de mantener**

### Pasos Rápidos

#### 1. Actualizar Command Line Tools (si es necesario)

Si tienes el error de Command Line Tools:

```bash
sudo rm -rf /Library/Developer/CommandLineTools
sudo xcode-select --install
```

Espera a que se instale (abrirá una ventana).

#### 2. Instalar Heroku

```bash
brew install heroku/brew/heroku
```

#### 3. Login

```bash
heroku login
```

#### 4. Crear Base de Datos

```bash
heroku create barcelona-housing
heroku addons:create heroku-postgresql:mini
```

#### 5. Migrar Datos

```bash
heroku pg:push barcelona_housing DATABASE_URL
```

#### 6. Obtener Credenciales

```bash
heroku pg:credentials:url
```

#### 7. Usar en Looker Studio

Usa las credenciales que te da Heroku (hostname, database, username, password).

## Alternativa: Port Forwarding en Router

Si no puedes usar Heroku (problemas con Command Line Tools):

### Pasos

1. **Accede a tu router**: `192.168.1.1` (o la IP de tu router)
2. **Busca "Port Forwarding"** o "Virtual Server"
3. **Añade regla**:
   - Puerto externo: `5432`
   - IP interna: `192.168.1.75`
   - Puerto interno: `5432`
   - Protocolo: `TCP`
4. **Guarda y reinicia router**
5. **En Looker Studio**:
   - Hostname: `37.133.54.161` (tu IP pública)
   - Port: `5432`
   - Database: `barcelona_housing`
   - Username: `adrianiraeguialvear`
   - Password: (tu contraseña de PostgreSQL)

### Verificar que Funciona

```bash
# Desde otra máquina o servicio online
psql -h 37.133.54.161 -p 5432 -U adrianiraeguialvear -d barcelona_housing
```

O visita: https://canyouseeme.org/ y prueba el puerto 5432

## Comparación de Soluciones

| Solución | Ventajas | Desventajas |
|----------|----------|-------------|
| **Heroku Postgres** | ✅ Fácil<br>✅ Sin configuración<br>✅ URL permanente | ⚠️ Requiere Command Line Tools<br>⚠️ Límite 10K filas (gratis) |
| **Port Forwarding** | ✅ Control total<br>✅ Sin límites | ❌ Requiere acceso al router<br>❌ IP puede cambiar |
| **cloudflared** | ✅ Gratis | ❌ No funciona bien con TCP |
| **ngrok** | ✅ Fácil | ❌ Requiere tarjeta para TCP |

## Recomendación

**Para desarrollo**: Usa **Heroku Postgres** (más fácil)

**Para producción**: Migra a **Google Cloud SQL** o **AWS RDS**

---

**¿Listo para migrar a Heroku?** Ejecuta:
```bash
./scripts/setup_heroku_postgres.sh
```
