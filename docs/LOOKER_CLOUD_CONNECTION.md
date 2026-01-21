# Conexión de Looker Cloud a PostgreSQL Local

## Situación

Estás accediendo a **Looker Cloud** (desde la web) y necesitas conectarlo a tu PostgreSQL local en tu Mac.

## Solución Recomendada: SSH Tunnel

Looker Cloud soporta **SSH Tunnels** para conectarse a bases de datos locales de forma segura.

### Paso 1: Habilitar SSH en tu Mac

1. **System Preferences** → **Sharing**
2. Activar **Remote Login**
3. Asegúrate de que tu usuario (`adrianiraeguialvear`) tiene permisos

**Verificar**:
```bash
# Deberías poder conectarte localmente
ssh adrianiraeguialvear@localhost
```

### Paso 2: Obtener tu IP Pública

Looker necesita tu IP pública para conectarse. Opciones:

**Opción A: Usar un servicio dinámico DNS** (recomendado si tu IP cambia):
- No-IP, DuckDNS, etc.

**Opción B: Usar tu IP pública actual**:
```bash
# Obtener tu IP pública
curl ifconfig.me
# o
curl ipinfo.io/ip
```

**⚠️ Importante**: Si tu IP cambia, necesitarás actualizar la configuración en Looker.

### Paso 3: Configurar Puerto en Router (si es necesario)

Si estás detrás de un router, necesitas hacer **port forwarding**:
- **Puerto externo**: 22 (SSH)
- **IP interna**: `192.168.1.75` (tu Mac)
- **Puerto interno**: 22

### Paso 4: Configurar en Looker

En Looker Cloud:

1. **Admin** → **Connections** → **New Connection**
2. Seleccionar **PostgreSQL**
3. Configurar **SSH Tunnel**:
   - **SSH Host**: Tu IP pública o dominio dinámico
   - **SSH Port**: `22`
   - **SSH Username**: `adrianiraeguialvear`
   - **SSH Authentication**: 
     - **Method**: Password (o SSH Key si prefieres)
     - **Password**: Tu contraseña de macOS

4. Configurar **Database Connection**:
   - **Host**: `localhost` (a través del túnel SSH)
   - **Port**: `5432`
   - **Database**: `barcelona_housing`
   - **Username**: `adrianiraeguialvear`
   - **Password**: (dejar vacío o configurar una contraseña en PostgreSQL)

5. **Test Connection**

## Alternativa: PostgreSQL en la Nube (Más Fácil)

Si el SSH Tunnel es complicado, considera migrar PostgreSQL a la nube:

### Opción A: Heroku Postgres (Gratis para desarrollo)

```bash
# Instalar Heroku CLI
brew install heroku/brew/heroku

# Login
heroku login

# Crear app y base de datos
heroku create barcelona-housing
heroku addons:create heroku-postgresql:mini

# Migrar datos
heroku pg:push barcelona_housing DATABASE_URL
```

Luego en Looker:
- **Host**: `tu-app.herokuapp.com`
- **Port**: `5432`
- **Database**: (proporcionado por Heroku)
- **Username/Password**: (proporcionados por Heroku)

### Opción B: Google Cloud SQL

1. Crear instancia Cloud SQL PostgreSQL
2. Migrar datos desde local
3. Conectar Looker directamente

### Opción C: AWS RDS

Similar a Google Cloud SQL.

## Configuración Rápida: PostgreSQL Remoto (No Recomendado para Producción)

Si quieres probar rápidamente sin SSH Tunnel:

### ⚠️ Advertencia: Esto expone tu base de datos a internet

### Paso 1: Configurar PostgreSQL para Escuchar en Todas las Interfaces

```bash
# Editar postgresql.conf
nano /opt/homebrew/var/postgresql@16/postgresql.conf
```

Cambiar:
```conf
listen_addresses = '*'
```

### Paso 2: Configurar pg_hba.conf

```bash
# Editar pg_hba.conf
nano /opt/homebrew/var/postgresql@16/pg_hba.conf
```

Añadir:
```
host    all             all             0.0.0.0/0               md5
```

### Paso 3: Configurar Contraseña

```bash
psql -d barcelona_housing
ALTER USER adrianiraeguialvear WITH PASSWORD 'contraseña_segura';
\q
```

### Paso 4: Reiniciar PostgreSQL

```bash
brew services restart postgresql@16
```

### Paso 5: Configurar Firewall

```bash
# Permitir PostgreSQL en firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/opt/postgresql@16/bin/postgres
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /opt/homebrew/opt/postgresql@16/bin/postgres
```

### Paso 6: En Looker

- **Host**: Tu IP pública (obtenida con `curl ifconfig.me`)
- **Port**: `5432`
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: La contraseña que configuraste

## Recomendación Final

**Para desarrollo/pruebas**: Usa **SSH Tunnel** (más seguro)

**Para producción**: Migra a **PostgreSQL en la nube** (Heroku, AWS RDS, Google Cloud SQL)

## Troubleshooting

### Error: "Connection timeout"

**Causa**: Firewall bloqueando o IP incorrecta.

**Solución**:
1. Verificar que tu IP pública es correcta
2. Verificar port forwarding en router
3. Verificar firewall de macOS

### Error: "SSH authentication failed"

**Causa**: Credenciales incorrectas o SSH no habilitado.

**Solución**:
1. Verificar Remote Login está activado
2. Probar conexión SSH localmente: `ssh adrianiraeguialvear@localhost`
3. Verificar usuario y contraseña

### Error: "Database connection failed"

**Causa**: PostgreSQL no accesible a través del túnel.

**Solución**:
1. Verificar que PostgreSQL está corriendo: `brew services list | grep postgresql`
2. Verificar que escucha en localhost: `netstat -an | grep 5432`
3. Probar conexión local: `psql -h localhost -d barcelona_housing`

---

**Última actualización**: 2026-01-10
