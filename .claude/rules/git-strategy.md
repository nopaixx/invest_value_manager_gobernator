# Git Strategy

> Se carga automáticamente con CLAUDE.md
> Aplica a AMBOS repos: gobernator (propio) e invest_value_manager (via instrucciones al especialista)

---

## Estrategia de Branches

```
master ← release/YYYY-MM ← develop ← feature/YYYY-MM-DD
```

### Feature branches (diario)
- Nombre: `feature/YYYY-MM-DD`
- Crear al inicio de cada día de trabajo desde `develop`
- Todo el trabajo del día va en esta branch
- Al cerrar el día: merge a `develop`

### Develop
- Branch de integración
- Recibe merges de features diarias
- Fuente para releases mensuales

### Release branches (mensual)
- Nombre: `release/YYYY-MM`
- Crear al inicio de cada mes desde `develop`
- Merge a `master` con la foto del mes
- Representan el estado del sistema al cierre de cada mes

### Master
- Siempre refleja la última release
- Solo recibe merges desde release branches

### Reglas
- NUNCA eliminar branches (feature ni release) - sirven de historial
- NUNCA hacer push --force
- Commits descriptivos que expliquen qué se hizo y por qué

---

## Para mi repo (gobernator)

Yo gestiono mi propio git directamente:
- Crear feature branch al inicio de cada día
- Commit con cambios de configuración, state, reglas
- Merge a develop al cerrar
- Release mensual

## Para el especialista (invest_value_manager)

Le pido via Telegram que:
- Cree `feature/YYYY-MM-DD` al inicio de cada día
- Haga commit y push de su trabajo
- Merge a develop al cerrar el día
- Cree release mensual

Esto me permite leer su repo (git log, diffs, ficheros) para:
- Ver qué cambios hizo sin preguntarle
- Verificar cumplimiento de principios en sus cambios
- Tener trazabilidad completa para Angel
