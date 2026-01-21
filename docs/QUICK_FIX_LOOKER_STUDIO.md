# Solución Rápida: Error de Port Forwarding en Cursor

## Problema

Error: `Unable to forward localhost:5432. spawn /Applications/Cursor.app/Contents/Resources/app/bin/code-tunnel ENOENT`

Este error ocurre cuando intentas usar port forwarding de Cursor y hay un problema con el ejecutable.

## Solución Rápida: Heroku Postgres (5 minutos)

La forma más fácil es migrar a Heroku Postgres, que es **gratis** y no requiere port forwarding.

### Paso 1: Instalar Heroku CLI

```bash
brew install heroku/brew/heroku
```

### Paso 2: Login

```bash
heroku login
```

Esto abrirá tu navegador para autenticarte.

### Paso 3: Crear Base de Datos

```bash
# Crear app (si no existe)
heroku create barcelona-housing

# Crear base de datos PostgreSQL (gratis)
heroku addons:create heroku-postgresql:mini
```

### Paso 4: Migrar Datos

```bash
# Migrar desde PostgreSQL local
heroku pg:push barcelona_housing DATABASE_URL
```

### Paso 5: Obtener Credenciales

```bash
# Ver URL completa
heroku config:get DATABASE_URL

# O ver credenciales parseadas
heroku pg:credentials:url
```

### Paso 6: Configurar en Looker Studio

La URL de Heroku tiene el formato:
```
postgres://usuario:contraseña@host:5432/database
```

**En Looker Studio**:
- **Hostname**: (extraer de la URL, ej: `ec2-xxx-xxx.compute-1.amazonaws.com`)
- **Port**: `5432`
- **Database**: (extraer de la URL)
- **Username**: (extraer de la URL)
- **Password**: (extraer de la URL)

**O usar JDBC URL directamente**:
```
jdbc:postgresql://host:5432/database
```

## Alternativa: ngrok (Para Pruebas Rápidas)

Si prefieres mantener PostgreSQL local:

### Paso 1: Instalar ngrok

```bash
brew install ngrok/ngrok/ngrok
```

### Paso 2: Crear Túnel

```bash
ngrok tcp 5432
```

Esto te dará algo como:
```
Forwarding  tcp://0.tcp.ngrok.io:12345 -> localhost:5432
```

### Paso 3: Usar en Looker Studio

**JDBC URL**:
```
jdbc:postgresql://0.tcp.ngrok.io:12345/barcelona_housing
```

**⚠️ Nota**: La URL de ngrok cambia cada vez que lo reinicias. Es solo para pruebas.

## Script Automático para Heroku

He creado un script que hace todo automáticamente:

```bash
./scripts/setup_heroku_postgres.sh
```

Este script:
1. Verifica/instala Heroku CLI
2. Te ayuda a hacer login
3. Crea la app y base de datos
4. Migra los datos
5. Te muestra las credenciales para Looker Studio

## Comparación de Opciones

| Opción | Ventajas | Desventajas |
|--------|----------|-------------|
| **Heroku Postgres** | ✅ Gratis<br>✅ Sin configuración<br>✅ URL permanente<br>✅ Funciona desde cualquier lugar | ⚠️ Límite de 10K filas (plan gratis) |
| **ngrok** | ✅ Rápido para pruebas<br>✅ Mantiene datos locales | ❌ URL cambia cada vez<br>❌ Solo para desarrollo |
| **Port Forwarding Router** | ✅ Control total<br>✅ Sin límites | ❌ Requiere acceso al router<br>❌ Configuración compleja |

## Recomendación

**Para desarrollo/pruebas**: Usa **Heroku Postgres** (más fácil y confiable)

**Para producción**: Migra a **Google Cloud SQL** o **AWS RDS**

---

**¿Listo para migrar a Heroku?** Ejecuta:
```bash
./scripts/setup_heroku_postgres.sh
```
