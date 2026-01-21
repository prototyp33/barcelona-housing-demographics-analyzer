# Usar cloudflared con PostgreSQL TCP

## Problema

Cloudflared muestra una URL HTTPS, pero PostgreSQL necesita TCP. Necesitamos obtener la URL TCP correcta.

## Solución: Usar el Hostname con Puerto TCP

Cloudflared crea un túnel TCP, pero muestra la URL HTTPS. Para PostgreSQL, usa:

**Hostname**: `scenarios-investigated-taxes-amended.trycloudflare.com`  
**Puerto TCP**: Cloudflared usa el mismo puerto que expones (5432), pero necesitas obtener el puerto TCP del túnel.

## Método 1: Verificar Puerto TCP en los Logs

Busca en los logs de cloudflared una línea que muestre el puerto TCP. Si no aparece, usa el método 2.

## Método 2: Usar el Hostname Directamente

Para TCP, cloudflared debería exponer el puerto directamente. Prueba:

**En Looker Studio - JDBC URL**:
```
jdbc:postgresql://scenarios-investigated-taxes-amended.trycloudflare.com:5432/barcelona_housing
```

**O BASIC Connection**:
- **Hostname**: `scenarios-investigated-taxes-amended.trycloudflare.com`
- **Port**: `5432`
- **Database**: `barcelona_housing`
- **Username**: `adrianiraeguialvear`
- **Password**: (tu contraseña de PostgreSQL)

## Método 3: Verificar Puerto TCP con netstat

En otra terminal, mientras cloudflared está corriendo:

```bash
netstat -an | grep cloudflared
```

Esto mostrará los puertos que cloudflared está usando.

## Nota Importante

El hostname `scenarios-investigated-taxes-amended.trycloudflare.com` cambiará cada vez que reinicies cloudflared. Mantén cloudflared corriendo mientras uses Looker Studio.

## Si No Funciona

Si el puerto 5432 no funciona directamente, cloudflared puede estar usando un puerto diferente. En ese caso:

1. Revisa los logs completos de cloudflared
2. Busca líneas que mencionen "TCP" o el puerto
3. O usa Heroku Postgres como alternativa permanente

---

**Tu URL actual**: `scenarios-investigated-taxes-amended.trycloudflare.com:5432`
