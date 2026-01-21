# Guía: Port Forwarding para Looker Studio

## Situación

- ❌ Heroku requiere tarjeta de crédito
- ❌ ngrok requiere tarjeta para TCP
- ❌ cloudflared no funciona bien con TCP
- ✅ **Port Forwarding en Router** - Solución permanente y gratuita

## Tu Información

- **IP Pública**: `37.133.54.161`
- **IP Local (Mac)**: `192.168.1.75`
- **Puerto PostgreSQL**: `5432`

## Pasos para Configurar Port Forwarding

### Paso 1: Acceder a tu Router

1. Abre un navegador
2. Ve a la IP de tu router. Prueba estas opciones comunes:
   - `192.168.1.1`
   - `192.168.0.1`
   - `10.0.0.1`
   - `192.168.1.254`

3. Si no sabes la IP de tu router:
   ```bash
   # En macOS
   netstat -nr | grep default
   # O
   route -n get default | grep gateway
   ```

4. Login con tus credenciales (si no las sabes, están en la etiqueta del router)

### Paso 2: Encontrar Port Forwarding

Busca una sección llamada:
- **"Port Forwarding"**
- **"Virtual Server"**
- **"NAT Forwarding"**
- **"Applications & Gaming"**
- **"Advanced" → "Port Forwarding"**

### Paso 3: Crear Regla de Port Forwarding

Añade una nueva regla con estos valores:

| Campo | Valor |
|-------|-------|
| **Nombre/Descripción** | `PostgreSQL Looker Studio` |
| **Puerto Externo** | `5432` |
| **Puerto Interno** | `5432` |
| **IP Interna** | `192.168.1.75` |
| **Protocolo** | `TCP` (o `Both`) |
| **Estado** | `Enabled` / `Activo` |

### Paso 4: Guardar y Aplicar

1. Guarda la configuración
2. Reinicia el router (opcional pero recomendado)
3. Espera 1-2 minutos a que el router reinicie

### Paso 5: Verificar que PostgreSQL Está Configurado

Asegúrate de que PostgreSQL está configurado para aceptar conexiones remotas:

```bash
# Verificar listen_addresses
grep listen_addresses /opt/homebrew/var/postgresql@16/postgresql.conf
# Debe mostrar: listen_addresses = '*'

# Verificar pg_hba.conf tiene IPs de Google
grep "142.251.74" /opt/homebrew/var/postgresql@16/pg_hba.conf
```

Si no está configurado, ejecuta:
```bash
./scripts/setup_postgresql_for_looker_studio.sh
```

### Paso 6: Verificar Port Forwarding

**Opción A: Desde otra máquina**
```bash
psql -h 37.133.54.161 -p 5432 -U adrianiraeguialvear -d barcelona_housing
```

**Opción B: Servicio online**
Visita: https://canyouseeme.org/
- Puerto: `5432`
- Debe mostrar "Success" si está abierto

### Paso 7: Configurar en Looker Studio

**BASIC Connection**:
- **Hostname or IP address**: `37.133.54.161`
- **Port**: `5432`
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: (tu contraseña de PostgreSQL)

**O JDBC URL**:
```
jdbc:postgresql://37.133.54.161:5432/barcelona_housing
```

## Troubleshooting

### Error: "Connection timeout"

**Causa**: Port forwarding no configurado o firewall bloqueando.

**Solución**:
1. Verifica que la regla de port forwarding está activa
2. Verifica que la IP interna es correcta (`192.168.1.75`)
3. Verifica firewall del router (puede tener firewall adicional)

### Error: "Password authentication failed"

**Causa**: Contraseña incorrecta.

**Solución**:
```bash
psql -d barcelona_housing
ALTER USER adrianiraeguialvear WITH PASSWORD 'nueva_contraseña_segura';
\q
```

### Error: "No route to host"

**Causa**: IP pública cambió o router bloqueando.

**Solución**:
1. Verifica IP pública actual: `curl ifconfig.me`
2. Si cambió, actualiza Looker Studio con la nueva IP
3. Considera usar un servicio DNS dinámico (No-IP, DuckDNS) para tener un hostname permanente

### Puerto 5432 no aparece abierto

**Posibles causas**:
1. ISP bloqueando puertos (algunos ISPs bloquean puertos comunes)
2. Router con firewall adicional
3. Port forwarding mal configurado

**Solución**: Prueba con otro puerto (ej: 5433) y cambia PostgreSQL para escuchar en ese puerto.

## Nota sobre IP Dinámica

Si tu IP pública cambia (IP dinámica), necesitarás actualizar Looker Studio cada vez.

**Solución**: Usa un servicio DNS dinámico:
1. Crea cuenta en No-IP o DuckDNS (gratis)
2. Configura un hostname (ej: `barcelona-housing.ddns.net`)
3. Configura tu router para actualizar el DNS automáticamente
4. Usa el hostname en Looker Studio en lugar de la IP

---

**Esta es la solución más permanente y no requiere tarjetas de crédito ni servicios externos.**
