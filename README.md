# Construction Intelligence V6

Dashboard Streamlit para convertir 2.392 líneas históricas de facturas de construcción en inteligencia de costos y compras.

## Cambios clave V6
- El histórico se interpreta como **4 casas construidas**, no 3.
- Las ventanas Casa 1–4 son **inferidas y editables**; no se divide el gasto automáticamente en partes iguales.
- El consolidado fuente está **sin impuesto de ventas**. El dashboard separa precio neto, impuesto estimado y costo final, con tasa configurable (13% por defecto).
- La planificación futura pasa a **Casas 5 y 6**.
- Nueva sección **Anatomía de la casa** con receta física: cocina, sala, patio, gradas, 2 dormitorios, baño completo, medio baño, puertas, ventanas, muebles de melamina y cubierta frontal de policarbonato.
- Melamina se identifica también por láminas/tableros, cortes y herrajes claramente atribuibles.
- Cubierta frontal agrupa policarbonato y componentes estructurales/fijaciones cuando la descripción lo permite.
- Fletes se muestran solo cuando existen cargos útiles reales.
- Cada gráfico conserva una explicación breve de lectura y decisión.
- Light/Dark y microanimaciones con `prefers-reduced-motion`.

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Nota metodológica
Las asignaciones por casa que dependen de ventanas de fechas son inferencias editables. La regla del 23/03/2026 para arena, block, piedra, cemento y varilla se conserva como evidencia directa de la última casa histórica (Casa 4).
