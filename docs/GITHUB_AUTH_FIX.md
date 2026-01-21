# 🔐 Solución para Problemas de Autenticación con GitHub

**Fecha**: 2026-01-10  
**Problema**: `git push` falla con "Invalid username or token"

---

## Problema Identificado

1. Variable de entorno `GITHUB_TOKEN` configurada pero inválida
2. Esta variable tiene prioridad sobre el token válido en el keyring
3. El token del keyring puede estar expirado o sin permisos adecuados

---

## Soluciones

### Opción 1: Regenerar Token de GitHub CLI (Recomendado)

```bash
# 1. Desactivar token inválido temporalmente
unset GITHUB_TOKEN

# 2. Regenerar token con permisos de repo
gh auth refresh -s repo -h github.com

# 3. Configurar Git para usar el token
gh auth setup-git

# 4. Verificar estado
gh auth status

# 5. Intentar push
git push origin main
```

### Opción 2: Crear Nuevo Token Personal

1. Ir a: https://github.com/settings/tokens
2. Click en "Generate new token" → "Generate new token (classic)"
3. Nombre: "Barcelona Housing Analyzer"
4. Scopes: Seleccionar `repo` (todos los permisos de repositorio)
5. Click "Generate token"
6. **Copiar el token inmediatamente** (solo se muestra una vez)

Luego en terminal:

```bash
# Opción A: Usar con GitHub CLI
echo "TU_TOKEN_AQUI" | gh auth login --with-token

# Opción B: Configurar manualmente
git config --global credential.helper osxkeychain
git push origin main
# Cuando pida credenciales:
# Username: prototyp33
# Password: [pegar el token]
```

### Opción 3: Usar SSH (Más Seguro a Largo Plazo)

```bash
# 1. Verificar si tienes clave SSH
ls -la ~/.ssh/id_*.pub

# 2. Si no tienes, generar una nueva:
ssh-keygen -t ed25519 -C "tu-email@example.com"
# Presionar Enter para ubicación por defecto
# Opcional: agregar passphrase

# 3. Copiar clave pública:
cat ~/.ssh/id_ed25519.pub | pbcopy

# 4. Agregar a GitHub:
# Ir a: https://github.com/settings/keys
# Click "New SSH key"
# Title: "MacBook Pro" (o el nombre que prefieras)
# Key: Pegar el contenido copiado
# Click "Add SSH key"

# 5. Verificar conexión:
ssh -T git@github.com
# Debería decir: "Hi prototyp33! You've successfully authenticated..."

# 6. Cambiar remote a SSH:
git remote set-url origin git@github.com:prototyp33/barcelona-housing-demographics-analyzer.git

# 7. Verificar:
git remote -v

# 8. Hacer push:
git push origin main
```

---

## Solución Temporal: Desactivar GITHUB_TOKEN

Si necesitas hacer push inmediatamente y no puedes regenerar el token:

```bash
# En la misma sesión de terminal:
unset GITHUB_TOKEN
git push origin main
```

**Nota**: Esto solo funciona en la sesión actual. Para hacerlo permanente, elimina `GITHUB_TOKEN` de tu archivo de configuración del shell (`~/.zshrc`, `~/.bashrc`, etc.).

---

## Verificar Configuración Actual

```bash
# Estado de autenticación
gh auth status

# Configuración de Git
git config --list | grep credential
git remote -v

# Variables de entorno
echo "GITHUB_TOKEN: ${GITHUB_TOKEN:+SET}"
```

---

## Prevención Futura

1. **No configurar `GITHUB_TOKEN` en variables de entorno** a menos que sea absolutamente necesario
2. **Usar GitHub CLI** (`gh auth`) para gestionar tokens automáticamente
3. **Usar SSH** para operaciones Git (más seguro y confiable)
4. **Regenerar tokens periódicamente** (cada 90 días recomendado)

---

## Referencias

- [GitHub CLI Authentication](https://cli.github.com/manual/gh_auth)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub SSH Keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

---

**Estado**: ⚠️ Pendiente de resolver por el usuario  
**Siguiente paso**: Ejecutar Opción 1 o 3 según preferencia
