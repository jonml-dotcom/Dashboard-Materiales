# Construction Intelligence V6.2

Esta versión corrige la metodología central del estudio.

## Regla principal de la receta
Las facturas corresponden a **4 casas esencialmente iguales**. La receta estándar por vivienda se calcula así:

- **Block, arena, cemento, piedra y varilla:** cantidades directas confirmadas de la última casa usando las compras posteriores al **23/03/2026**.
- **Resto de materiales y consumibles de obra atribuibles a las viviendas:** cantidad y costo consolidado de las 4 casas **÷ 4**.
- Se excluyen de la receta base herramientas/equipo, servicios, líneas no incorporadas y registros ambiguos; fletes se analizan aparte cuando existen datos útiles.

## Cambios V6.2
- La **Receta de una casa** pasa a ser la primera sección y núcleo del dashboard.
- Se elimina la lectura fuerte de costos Casa 1→Casa 4 basada en ventanas arbitrarias de fechas.
- Las fechas se usan principalmente para **evolución de precios y momento de compra**.
- Se corrigió un error de V6: el costo de materiales estimados total÷4 ahora también se divide entre 4, no solo la cantidad.
- La receta muestra `Confirmado` vs `Estimado`, trazabilidad de líneas y cantidad total de las 4 casas.
- Casas 5 y 6 parten directamente de esta receta, más margen de seguridad y precios/proveedores comparables.
- Precio sin impuesto e impuesto estimado permanecen claramente diferenciados.
- Fletes desaparecen automáticamente si no existen cargos reales útiles.


## Nuevo en V6.2
- Se reincorpora una visualización de **tendencia de disminución/aumento del costo**, pero sin reconstruir artificialmente Casa 1–4.
- El gráfico mantiene fija la **receta estándar de una vivienda** y la revaloriza con precios históricos por mes.
- Se muestran dos lecturas: **costo estimado de la receta** e **índice de costo (base 100)**.
- Solo se muestran meses con al menos **70% de cobertura** de la canasta de referencia para evitar conclusiones con datos demasiado incompletos.
