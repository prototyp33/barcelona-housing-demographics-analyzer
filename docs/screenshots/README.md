# 📸 Screenshots del Dashboard

Este directorio contiene capturas de pantalla del dashboard para documentación y showcase.

## Organización

```
screenshots/
├── dashboard/           # Capturas del dashboard principal
│   ├── home.png
│   ├── map-view.png
│   └── analysis.png
├── features/            # Capturas por feature
│   ├── calculator/
│   ├── clustering/
│   └── predictions/
└── demos/               # GIFs animados para demos
    └── quick-tour.gif
```

## Convenciones de Nombres

- Usar kebab-case: `feature-name-view.png`
- Incluir fecha para versiones: `home-2025-01.png`
- Resolución recomendada: 1920x1080 o 1280x720

## Herramientas Recomendadas

- **macOS:** CMD+Shift+5 o CleanShot X
- **Windows:** Win+Shift+S o ShareX
- **Linux:** Flameshot o GNOME Screenshot

## Uso en Documentación

```markdown
![Dashboard Home](docs/screenshots/dashboard/home.png)
```

## GIFs para Demos

Para crear GIFs animados:
1. Grabar con OBS o LICEcap
2. Optimizar con gifsicle
3. Máximo 5MB para GitHub README

