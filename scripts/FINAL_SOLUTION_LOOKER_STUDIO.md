# Solución Final para Looker Studio

## Resumen del Problema

- ❌ Port forwarding de Cursor no funciona
- ❌ ngrok requiere tarjeta de crédito para TCP
- ❌ cloudflared quick tunnels no exponen TCP correctamente

## Solución Definitiva: Heroku Postgres

### Ventajas
- ✅ Gratis para desarrollo
- ✅ Funciona directamente con Looker Studio (sin túnel)
- ✅ URL permanente (no cambia)
- ✅ Sin configuración de router/firewall
- ✅ Fácil de mantener

### Pasos

#### 1. Actualizar Command Line Tools (si es necesario)

Si tienes el error de Command Line Tools:

```bash
sudo rm -rf /Library/Developer/CommandLineTools
sudo xcode-select --install
```

Esto abrirá una ventana para instalar. Espera a que termine.

#### 2. Instalar Heroku CLI

```bash
brew install heroku/brew/heroku
```

#### 3. Login en Heroku

```bash
heroku login
```

Esto abrirá tu navegador para autenticarte.

#### 4. Crear App y Base de Datos

```bash
# Crear app
heroku create barcelona-housing

# Crear base de datos PostgreSQL (gratis)
heroku addons:create heroku-postgresql:mini
```

#### 5. Migrar Datos

```bash
# Migrar desde PostgreSQL local
heroku pg:push barcelona_housing DATABASE_URL
```

Esto puede tardar unos minutos dependiendo del tamaño de tus datos.

#### 6. Obtener Credenciales

```bash
# Ver URL completa
heroku config:get DATABASE_URL

# O ver credenciales parseadas
heroku pg:credentials:url
```

La URL tiene el formato:
```
postgres://usuario:contraseña@host:5432/database
```

#### 7. Configurar en Looker Studio

**JDBC URL**:
```
jdbc:postgresql://host:5432/database
```

**O BASIC Connection**:
- **Hostname**: (extraer de la URL)
- **Port**: `5432`
- **Database**: (extraer de la URL)
- **Username**: (extraer de la URL)
- **Password**: (extraer de la URL)

## Script Automático

He creado un script que hace todo automáticamente:

```bash
./scripts/setup_heroku_postgres.sh
```

## Si Command Line Tools es un Problema

Si no puedes actualizar Command Line Tools, la única alternativa es:

**Configurar Port Forwarding en tu Router**:
1. Accede a tu router (192.168.1.1)
2. Configura port forwarding: 5432 → 192.168.1.75:5432
3. En Looker Studio usa: `37.133.54.161:5432`

---

**Recomendación Final**: Heroku Postgres es la solución más simple y confiable.
