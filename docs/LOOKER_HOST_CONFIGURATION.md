# Configuración del Host para Looker - PostgreSQL

## Hostname Actual

**Hostname**: `localhost` (solo conexiones locales)

PostgreSQL está configurado para escuchar solo en `localhost`, lo que significa que solo acepta conexiones desde la misma máquina.

## Opciones de Conexión

### Opción 1: Looker en la Misma Máquina (Local)

Si Looker está instalado en tu Mac:

**Configuración en Looker**:
- **Host**: `localhost` o `127.0.0.1`
- **Port**: `5432`
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: (dejar vacío si usa autenticación peer)

### Opción 2: Looker en Otra Máquina o Cloud

Si Looker está en otra máquina o en la nube (Looker Cloud), necesitas:

1. **Obtener tu IP local**:
   ```bash
   # En macOS
   ipconfig getifaddr en0
   # o
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **Configurar PostgreSQL para aceptar conexiones remotas** (ver abajo)

3. **Usar tu IP local o hostname**:
   - **Host**: `macbook-pro.home` (tu hostname) o tu IP local (ej: `192.168.1.xxx`)
   - **Port**: `5432`
   - **Database**: `barcelona_housing`
   - **Username**: `adrianiraeguialvear`
   - **Password**: (necesitarás configurar contraseña)

## Configurar PostgreSQL para Conexiones Remotas

Si necesitas que Looker se conecte desde otra máquina:

### Paso 1: Editar `postgresql.conf`

```bash
# Encontrar el archivo de configuración
psql -d barcelona_housing -c "SHOW config_file;"

# Editar (generalmente en):
nano /opt/homebrew/var/postgresql@16/postgresql.conf
```

Cambiar:
```conf
# De:
#listen_addresses = 'localhost'

# A:
listen_addresses = '*'  # o tu IP específica
```

### Paso 2: Editar `pg_hba.conf`

```bash
# Encontrar el archivo
psql -d barcelona_housing -c "SHOW hba_file;"

# Editar (generalmente en):
nano /opt/homebrew/var/postgresql@16/pg_hba.conf
```

Añadir al final:
```
# Permitir conexiones desde cualquier IP (ajustar según seguridad)
host    all             all             0.0.0.0/0               md5
```

### Paso 3: Configurar Contraseña para el Usuario

```bash
psql -d barcelona_housing

# En psql:
ALTER USER adrianiraeguialvear WITH PASSWORD 'tu_contraseña_segura';
\q
```

### Paso 4: Reiniciar PostgreSQL

```bash
brew services restart postgresql@16
```

### Paso 5: Verificar que Escucha en Todas las Interfaces

```bash
netstat -an | grep 5432
# Deberías ver algo como: *.5432 o 0.0.0.0.5432
```

## Configuración Recomendada para Looker Cloud

Si Looker está en la nube, las opciones son:

### Opción A: SSH Tunnel (Más Seguro)

1. Crear túnel SSH desde Looker a tu Mac:
   ```bash
   # En tu Mac, permitir conexiones SSH remotas
   # System Preferences → Sharing → Remote Login
   ```

2. En Looker, usar SSH tunnel:
   - **SSH Host**: Tu IP pública o dominio
   - **SSH Port**: 22
   - **SSH User**: `adrianiraeguialvear`
   - **Database Host**: `localhost` (a través del túnel)
   - **Database Port**: 5432

### Opción B: PostgreSQL en la Nube (Recomendado para Producción)

Migrar PostgreSQL a un servicio en la nube:
- **AWS RDS**
- **Google Cloud SQL**
- **Azure Database for PostgreSQL**
- **Heroku Postgres**

Luego conectar Looker directamente a ese servicio.

## Verificar Conexión

### Desde Terminal Local

```bash
# Probar conexión local
psql -h localhost -d barcelona_housing -U adrianiraeguialvear

# Probar conexión remota (desde otra máquina)
psql -h macbook-pro.home -d barcelona_housing -U adrianiraeguialvear
```

### Desde Looker

En Looker, usar "Test Connection" para verificar.

## Resumen Rápido

**Para conexión local (Looker en tu Mac)**:
- Host: `localhost`
- Port: `5432`
- Database: `barcelona_housing`
- User: `adrianiraeguialvear`
- Password: (vacío)

**Para conexión remota (Looker en otra máquina)**:
- Host: `macbook-pro.home` o tu IP local
- Port: `5432`
- Database: `barcelona_housing`
- User: `adrianiraeguialvear`
- Password: (configurar contraseña primero)

## Troubleshooting

### Error: "Connection refused"

**Causa**: PostgreSQL no está escuchando en esa dirección.

**Solución**:
1. Verificar que PostgreSQL está corriendo: `brew services list | grep postgresql`
2. Verificar `listen_addresses` en `postgresql.conf`
3. Reiniciar PostgreSQL: `brew services restart postgresql@16`

### Error: "Password authentication failed"

**Causa**: Contraseña incorrecta o usuario no existe.

**Solución**:
1. Verificar usuario: `psql -d barcelona_housing -c "\du"`
2. Configurar contraseña: `ALTER USER adrianiraeguialvear WITH PASSWORD 'nueva_contraseña';`

### Error: "No route to host"

**Causa**: Firewall bloqueando conexiones o IP incorrecta.

**Solución**:
1. Verificar IP: `ipconfig getifaddr en0`
2. Verificar firewall: System Preferences → Security & Privacy → Firewall
3. Añadir excepción para PostgreSQL

---

**Última actualización**: 2026-01-10
