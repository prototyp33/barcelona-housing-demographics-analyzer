# Conexión de Looker Studio a PostgreSQL Local

## Situación

Estás usando **Looker Studio** (Google Data Studio) desde la web y necesitas conectarlo a tu PostgreSQL local.

## Requisitos de Looker Studio

Looker Studio necesita:
- ✅ **Hostname o IP pública** accesible desde internet
- ✅ **Puerto 5432** abierto en firewall
- ✅ **Permitir conexiones desde IPs de Google**: `142.251.74.0/23`

## Opción 1: Configurar PostgreSQL para Conexiones Públicas (Recomendado)

### Paso 1: Configurar PostgreSQL para Escuchar en Todas las Interfaces

```bash
# Editar postgresql.conf
nano /opt/homebrew/var/postgresql@16/postgresql.conf
```

Buscar y cambiar:
```conf
# De:
#listen_addresses = 'localhost'

# A:
listen_addresses = '*'
```

### Paso 2: Configurar pg_hba.conf para Permitir IPs de Google

```bash
# Editar pg_hba.conf
nano /opt/homebrew/var/postgresql@16/pg_hba.conf
```

Añadir al final (antes de las líneas existentes):
```
# Permitir conexiones desde Looker Studio (IPs de Google)
host    all             all             142.251.74.0/23          md5
host    all             all             2001:4860:4807::/48       md5
```

### Paso 3: Configurar Contraseña para el Usuario

```bash
psql -d barcelona_housing

# En psql:
ALTER USER adrianiraeguialvear WITH PASSWORD 'contraseña_segura_123';
\q
```

### Paso 4: Reiniciar PostgreSQL

```bash
brew services restart postgresql@16
```

### Paso 5: Configurar Firewall de macOS

```bash
# Permitir PostgreSQL en firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/opt/postgresql@16/bin/postgres
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /opt/homebrew/opt/postgresql@16/bin/postgres
```

### Paso 6: Configurar Port Forwarding en Router

**⚠️ IMPORTANTE**: Necesitas configurar tu router para redirigir el puerto 5432 a tu Mac.

1. Accede a la configuración de tu router (generalmente `192.168.1.1`)
2. Busca "Port Forwarding" o "Virtual Server"
3. Añade regla:
   - **Puerto externo**: `5432`
   - **IP interna**: `192.168.1.75` (tu Mac)
   - **Puerto interno**: `5432`
   - **Protocolo**: TCP

### Paso 7: Obtener tu IP Pública

```bash
curl ifconfig.me
# Tu IP: 37.133.54.161
```

**⚠️ Nota**: Si tu IP cambia (IP dinámica), necesitarás actualizar la configuración en Looker Studio. Considera usar un servicio DNS dinámico.

### Paso 8: Configurar en Looker Studio

1. **Looker Studio** → **Create** → **Data Source**
2. Seleccionar **PostgreSQL**
3. Configurar conexión:

**BASIC Connection**:
- **Hostname or IP address**: `37.133.54.161` (tu IP pública)
- **Port**: `5432`
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: `contraseña_segura_123` (la que configuraste)

**O JDBC URL**:
```
jdbc:postgresql://37.133.54.161:5432/barcelona_housing
```

4. **AUTHENTICATE**
5. Seleccionar tabla (ej: `dim_barrios` o `fact_precios`)
6. **CONNECT**

## Opción 2: PostgreSQL en la Nube (Más Fácil y Seguro)

Para evitar configurar firewall y port forwarding, migra a PostgreSQL en la nube:

### Heroku Postgres (Gratis para desarrollo)

```bash
# Instalar Heroku CLI
brew install heroku/brew/heroku

# Login
heroku login

# Crear app y base de datos
heroku create barcelona-housing
heroku addons:create heroku-postgresql:mini

# Obtener URL de conexión
heroku config:get DATABASE_URL

# Migrar datos desde PostgreSQL local
heroku pg:push barcelona_housing DATABASE_URL
```

Luego en Looker Studio:
- **Hostname**: (proporcionado por Heroku, ej: `ec2-xxx-xxx-xxx.compute-1.amazonaws.com`)
- **Port**: `5432`
- **Database**: (proporcionado por Heroku)
- **Username/Password**: (proporcionados por Heroku)

### Google Cloud SQL (Nativo para Looker Studio)

1. Crear instancia Cloud SQL PostgreSQL
2. Migrar datos
3. Conectar Looker Studio directamente (sin configuración adicional)

## Opción 3: Usar Custom Query en Looker Studio

Si solo necesitas datos específicos, puedes usar **CUSTOM QUERY**:

```sql
SELECT 
    b.barrio_nombre,
    b.distrito_nombre,
    AVG(p.precio_m2_venta) as precio_promedio,
    COUNT(*) as num_registros
FROM fact_precios p
JOIN dim_barrios b ON p.barrio_id = b.barrio_id
WHERE p.anio = 2024
GROUP BY b.barrio_nombre, b.distrito_nombre
ORDER BY precio_promedio DESC
```

## Script de Configuración Automática

He creado un script para automatizar la configuración:

```bash
./scripts/setup_postgresql_for_looker_studio.sh
```

## Verificar Configuración

### Verificar que PostgreSQL Escucha en Todas las Interfaces

```bash
netstat -an | grep 5432
# Deberías ver: *.5432 o 0.0.0.0.5432
```

### Verificar que pg_hba.conf está Configurado

```bash
grep "142.251.74" /opt/homebrew/var/postgresql@16/pg_hba.conf
```

### Probar Conexión desde Internet

```bash
# Desde otra máquina o servicio online
psql -h 37.133.54.161 -p 5432 -U adrianiraeguialvear -d barcelona_housing
```

## Seguridad

⚠️ **ADVERTENCIAS**:

1. **Exponer PostgreSQL a internet es un riesgo de seguridad**
2. Usa contraseñas fuertes
3. Considera usar SSL/TLS (habilitar en Looker Studio)
4. Limita acceso solo a IPs de Google cuando sea posible
5. Para producción, usa PostgreSQL en la nube

## Troubleshooting

### Error: "Connection timeout"

**Causa**: Firewall o port forwarding no configurado.

**Solución**:
1. Verificar port forwarding en router
2. Verificar firewall de macOS
3. Verificar que PostgreSQL escucha en `*`

### Error: "Password authentication failed"

**Causa**: Contraseña incorrecta o usuario no existe.

**Solución**:
```bash
psql -d barcelona_housing
ALTER USER adrianiraeguialvear WITH PASSWORD 'nueva_contraseña';
```

### Error: "No route to host"

**Causa**: IP pública incorrecta o router bloqueando.

**Solución**:
1. Verificar IP pública: `curl ifconfig.me`
2. Verificar port forwarding
3. Verificar que tu IP no cambió

### Looker Studio no puede conectar

**Verificar**:
1. IPs de Google están en pg_hba.conf: `142.251.74.0/23`
2. PostgreSQL está corriendo: `brew services list | grep postgresql`
3. Puerto 5432 está abierto: `netstat -an | grep 5432`

## Recomendación Final

**Para desarrollo/pruebas**: Configura PostgreSQL local con las IPs de Google

**Para producción**: Migra a **Google Cloud SQL** o **Heroku Postgres**

---

**Última actualización**: 2026-01-10  
**Tu IP Pública**: 37.133.54.161  
**IPs de Google a permitir**: 142.251.74.0/23
