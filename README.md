# Dashboard Construcción V5

## Cambios principales
- Compatibilidad Light/Dark mediante variables del tema de Streamlit y `template="streamlit"` en Plotly.
- Varias opciones de visualización funcionales en cada análisis.
- Explicación breve de cómo leer cada gráfico y qué decisión ayuda a tomar.
- Evolución de precios por producto/presentación comparable; clavos EPA se consideran paquete/bolsa y no pieza individual.
- Fletes condicionales: solo aparece la pestaña si existen cargos reales útiles. En la base actual existen 19 cargos > ₡1.
- Casa 4/5 incorpora microanimación de etapas, interpretación automática y señales de compra.
- Material × proveedor usa MIN, MAX y TOTAL gastado; sin promedio ni mediana.
- Bolsas/sacos usan precio por kg cuando el peso está identificado.
- Contrapiso no se muestra como etapa independiente.
- Superbloque se mantiene separado del block convencional.

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app.py
```
