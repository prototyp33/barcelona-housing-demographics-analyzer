# Troubleshooting: Error de Conexión Looker Studio

## Problema Identificado

El diagnóstico muestra que:
- ✅ PostgreSQL está bien configurado localmente
- ✅ Escucha en todas las interfaces
- ✅ IPs de Google están permitidas
- ❌ **Puerto 5432 NO es accesible desde internet**

## Causa Principal

**Port Forwarding no configurado en el router** o **ISP bloqueando puertos**.

## Solución 1: Configurar Port Forwarding (Recomendado si tienes acceso al router)

### Paso 1: Acceder a tu Router

1. Abre un navegador
2. Ve a la IP de tu router (generalmente):
   - `192.168.1.1`
   - `192.168.0.1`
   - `10.0.0.1`
3. Login con tus credenciales (si no las sabes, están en la etiqueta del router)

### Paso 2: Configurar Port Forwarding

Busca una sección llamada:
- "Port Forwarding"
- "Virtual Server"
- "NAT Forwarding"
- "Applications & Gaming" (en algunos routers)

Añade una nueva regla:
- **Nombre/Descripción**: `PostgreSQL Looker Studio`
- **Puerto externo**: `5432`
- **Puerto interno**: `5432`
- **IP interna**: `192.168.1.75` (tu Mac)
- **Protocolo**: `TCP`
- **Estado**: `Enabled`

### Paso 3: Guardar y Reiniciar Router

1. Guarda la configuración
2. Reinicia el router (opcional pero recomendado)

### Paso 4: Verificar

```bash
# Desde otra máquina o servicio online (ej: canyouseeme.org)
# Debería mostrar que el puerto 5432 está abierto
```

## Solución 2: Usar Heroku Postgres (Más Fácil - Recomendado)

Si no puedes configurar el router o tu ISP bloquea puertos, migra a Heroku:

### Paso 1: Instalar Heroku CLI

```bash
brew install heroku/brew/heroku
```

### Paso 2: Login y Crear Base de Datos

```bash
# Login
heroku login

# Crear app (si no existe)
heroku create barcelona-housing

# Crear base de datos PostgreSQL (gratis para desarrollo)
heroku addons:create heroku-postgresql:mini
```

### Paso 3: Migrar Datos

```bash
# Obtener URL de conexión de Heroku
heroku config:get DATABASE_URL

# Migrar datos desde PostgreSQL local
heroku pg:push barcelona_housing DATABASE_URL
```

### Paso 4: Obtener Credenciales para Looker Studio

```bash
# Ver todas las variables de entorno
heroku config

# O específicamente la URL de la base de datos
heroku pg:credentials:url
```

La URL tiene el formato:
```
postgres://usuario:contraseña@host:5432/database
```

### Paso 5: Configurar en Looker Studio

**BASIC Connection**:
- **Hostname**: (extraer de la URL de Heroku, ej: `ec2-xxx-xxx.compute-1.amazonaws.com`)
- **Port**: `5432`
- **Database**: (extraer de la URL)
- **Username**: (extraer de la URL)
- **Password**: (extraer de la URL)

**O JDBC URL**:
```
jdbc:postgresql://host:5432/database
```

## Solución 3: Usar ngrok (Túnel Temporal)

Para pruebas rápidas sin configurar router:

### Paso 1: Instalar ngrok

```bash
brew install ngrok/ngrok/ngrok
```

### Paso 2: Crear Túnel

```bash
# Crear túnel al puerto 5432
ngrok tcp 5432
```

Esto te dará una URL como: `tcp://0.tcp.ngrok.io:12345`

### Paso 3: Configurar en Looker Studio

**JDBC URL**:
```
jdbc:postgresql://0.tcp.ngrok.io:12345/barcelona_housing
```

**⚠️ Nota**: ngrok es para desarrollo/pruebas. La URL cambia cada vez que reinicias ngrok.

## Errores Comunes y Soluciones

### Error: "Connection timeout"

**Causa**: Port forwarding no configurado o puerto bloqueado.

**Solución**:
1. Verifica port forwarding en router
2. Verifica que tu IP pública no cambió: `curl ifconfig.me`
3. Considera usar Heroku Postgres

### Error: "Password authentication failed"

**Causa**: Contraseña incorrecta.

**Solución**:
```bash
psql -d barcelona_housing
ALTER USER adrianiraeguialvear WITH PASSWORD 'nueva_contraseña_segura';
\q
```

### Error: "No route to host"

**Causa**: IP incorrecta o router bloqueando.

**Solución**:
1. Verifica IP pública: `curl ifconfig.me`
2. Verifica port forwarding
3. Usa Heroku Postgres como alternativa

### Error: "Connection refused"

**Causa**: PostgreSQL no está escuchando o firewall bloqueando.

**Solución**:
```bash
# Verificar que PostgreSQL está corriendo
brew services list | grep postgresql

# Verificar que escucha en todas las interfaces
grep listen_addresses /opt/homebrew/var/postgresql@16/postgresql.conf
```

## Verificación Rápida

### Desde tu Mac

```bash
# Debería funcionar
psql -h localhost -d barcelona_housing -U adrianiraeguialvear
```

### Desde Internet (si port forwarding está configurado)

```bash
# Reemplaza con tu IP pública
psql -h 37.133.54.161 -p 5432 -U adrianiraeguialvear -d barcelona_housing
```

### Usar Servicio Online

Visita: https://canyouseeme.org/
- Puerto: `5432`
- Debería mostrar "Success" si el puerto está abierto

## Recomendación Final

**Para desarrollo/pruebas rápidas**: Usa **Heroku Postgres** (gratis, sin configuración de router)

**Para producción**: Usa **Google Cloud SQL** o **AWS RDS** (mejor rendimiento y seguridad)

---

**Última actualización**: 2026-01-10
