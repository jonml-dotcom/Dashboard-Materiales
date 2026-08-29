from pathlib import Path
import math, re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Construir Mejor", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")
BASE = Path(__file__).with_name("base_maestra_homologada_2392.csv")
RECIPE_TYPES = ["Material permanente", "Material/consumible", "Consumible de obra"]
CORE_LABELS = {
    "Cemento gris 50 kg", "Arena", "Piedra / agregado", "Varilla #3", "Varilla #4",
    "Block concreto 12x20x40", "Block concreto 15x20x40"
}
STAGE_PLAN = [
    ("Preparación y cimentación",1,3),("Estructura",3,8),("Mampostería",5,10),("Cubierta",8,11),
    ("Hidrosanitario",8,13),("Eléctrico",9,14),("Repellos y preparación",12,16),("Cielos y divisiones",14,18),
    ("Pisos y enchapes",17,20),("Pintura",18,22),("Carpintería y acabados",20,23),("Sanitarios y cierre",20,24)
]

st.markdown("""<style>
:root{color-scheme:light dark}.block-container{padding-top:1rem;padding-bottom:3rem;max-width:1550px}
.hero{padding:24px 28px;border-radius:23px;background:linear-gradient(135deg,color-mix(in srgb,var(--primary-color) 17%,var(--background-color)),color-mix(in srgb,var(--secondary-background-color) 94%,var(--background-color)));border:1px solid color-mix(in srgb,var(--text-color) 13%,transparent);margin-bottom:15px}
.hero .eyebrow{font-size:.75rem;letter-spacing:.16em;text-transform:uppercase;opacity:.62}.hero h1{font-size:2.15rem;margin:.18rem 0 .35rem}.hero p{opacity:.78;margin:0;max-width:1000px}
.story-flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0 19px}
.story-step{position:relative;padding:15px 16px;border-radius:18px;background:var(--secondary-background-color);border:1px solid color-mix(in srgb,var(--text-color) 12%,transparent);min-height:110px}
.story-step .n{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;opacity:.55}
.story-step .big{font-size:1.2rem;font-weight:850;margin:.2rem 0}
.story-step .small{font-size:.79rem;opacity:.68}
.story-step:not(:last-child):after{content:'→';position:absolute;right:-10px;top:40%;font-size:1.2rem;font-weight:900;z-index:2}
.story-callout{padding:17px 19px;border-radius:18px;border:1px solid color-mix(in srgb,var(--primary-color) 35%,var(--text-color));background:color-mix(in srgb,var(--primary-color) 8%,var(--secondary-background-color));margin:10px 0 18px}
.story-callout .headline{font-size:1.05rem;font-weight:850;margin-bottom:5px}
@media(max-width:900px){.story-flow{grid-template-columns:1fr 1fr}.story-step:not(:last-child):after{display:none}}
@media(max-width:600px){.story-flow{grid-template-columns:1fr}}
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:10px 0 18px}.kpi,.card,.explain,.sourcebox{background:var(--secondary-background-color);border:1px solid color-mix(in srgb,var(--text-color) 12%,transparent)}
.kpi{border-radius:18px;padding:15px 17px}.kpi .label{font-size:.72rem;opacity:.62;text-transform:uppercase;letter-spacing:.08em}.kpi .value{font-size:1.45rem;font-weight:820;margin-top:3px}.kpi .sub{font-size:.78rem;opacity:.62;margin-top:3px}
.card{border-radius:18px;padding:14px 16px;margin:7px 0}.card .title{font-weight:820}.card .meta{font-size:.82rem;opacity:.67;margin-top:3px}.explain,.sourcebox{border-radius:14px;padding:11px 14px;margin:7px 0 16px;font-size:.86rem}.sourcebox{border-style:dashed}.chip{display:inline-block;padding:5px 9px;border-radius:999px;background:color-mix(in srgb,var(--primary-color) 13%,var(--secondary-background-color));font-size:.74rem;margin:2px 3px 2px 0}
[data-testid="stDataFrame"]{border-radius:15px;overflow:hidden;border:1px solid color-mix(in srgb,var(--text-color) 12%,transparent)}
@media(max-width:900px){.kpi-grid{grid-template-columns:1fr 1fr}.hero h1{font-size:1.65rem}}@media(max-width:600px){.kpi-grid{grid-template-columns:1fr}}
</style>""", unsafe_allow_html=True)

def money(v):
    return "—" if pd.isna(v) else f"₡{v:,.0f}".replace(",", ".")
def pct(v):
    return "—" if pd.isna(v) or not np.isfinite(v) else f"{v:+.1f}%"
def explain(read, decision):
    st.markdown(f"<div class='explain'><b>Cómo leerlo:</b> {read}<br><b>Qué decisión ayuda a tomar:</b> {decision}</div>", unsafe_allow_html=True)
def clean(s):
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9/#.xáéíóúñ\s]+"," ",str(s).lower())).strip()

def extract_size(desc):
    s=clean(desc)
    patterns=[r'\b\d+(?:\.\d+)?x\d+(?:\.\d+)?(?:x\d+(?:\.\d+)?)?\b',r'\b\d+\s+\d+/\d+\b',r'\b\d+/\d+\b',r'\b\d+(?:\.\d+)?\s*mm\b',r'\b\d+(?:\.\d+)?\s*cm\b',r'\b#\s*\d+\b']
    for pat in patterns:
        m=re.search(pat,s)
        if m: return m.group(0)
    return ''

def commercial_unit(row):
    d=clean(row.get('Descripcion_original','')); mat=clean(row.get('Material_homologado','')); prov=clean(row.get('Proveedor','')); pres=str(row.get('Presentacion','') or '')
    if pd.notna(row.get('Kg_por_unidad')) and float(row.get('Kg_por_unidad') or 0)>0: return pres or 'Unidad con peso conocido'
    for word,label in [('paquete','Paquete'),('bolsa','Bolsa'),('caja','Caja'),('rollo','Rollo'),('juego','Juego'),('set','Set')]:
        if word in d: return label
    if 'clavo' in mat and 'epa' in prov: return 'Paquete/bolsa EPA'
    return pres if pres and pres!='nan' else 'Unidad comercial'

def comparable_key(row):
    mat=str(row.get('Material_homologado','')); size=extract_size(row.get('Descripcion_original','')); unit=str(row.get('Unidad_comercial',''))
    parts=[mat]
    if size: parts.append(size)
    if unit: parts.append(unit)
    return ' · '.join(parts)

def add_component(d):
    x=d.copy()
    txt=(x.Material_homologado.fillna('')+' '+x.Familia.fillna('')+' '+x.Descripcion_original.fillna('')).str.lower()
    x['Componente_fisico']='Otros materiales de la vivienda'
    x.loc[txt.str.contains(r'melamin|mueble|closet|gabinet|bisagra|tapacanto|corredera',regex=True),'Componente_fisico']='Carpintería / muebles de melamina'
    x.loc[txt.str.contains(r'policarbon|cubierta|lamina techo|perfil h base|edpm',regex=True),'Componente_fisico']='Cubierta frontal / techo'
    x.loc[txt.str.contains(r'inodoro|lavaman|ducha|sanitari|grifer',regex=True),'Componente_fisico']='Baños / aparatos sanitarios'
    x.loc[txt.str.contains(r'puerta|cerradura|marco puerta|tope puerta',regex=True),'Componente_fisico']='Puertas y herrajes'
    x.loc[txt.str.contains(r'ventana|vidrio|espejo',regex=True),'Componente_fisico']='Ventanas / vidrio'
    x.loc[txt.str.contains(r'block|cemento|arena|piedra|varilla|acero refuerzo',regex=True),'Componente_fisico']='Estructura y obra gris'
    x.loc[txt.str.contains(r'cable|conduit|tomacorr|interruptor|breaker|electr',regex=True),'Componente_fisico']='Instalación eléctrica'
    x.loc[txt.str.contains(r'pvc|tuber|sifon|hidro|plomer',regex=True),'Componente_fisico']='Instalación hidrosanitaria'
    x.loc[txt.str.contains(r'pintura|sellador|esmalte|brocha|rodillo',regex=True),'Componente_fisico']='Pintura y acabados'
    x.loc[txt.str.contains(r'porcel|ceram|piso|enchape|fragüe|frague|bondex',regex=True),'Componente_fisico']='Pisos y enchapes'
    return x

@st.cache_data(show_spinner=False)
def load_data():
    d=pd.read_csv(BASE)
    d['Fecha']=pd.to_datetime(d['Fecha'],errors='coerce')
    for c in ['Cantidad','Precio_unitario','Total_linea','Kg_por_unidad','Precio_por_kg','Relevancia']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    for c in ['Proveedor','Factura','Descripcion_original','Material_homologado','Familia','Tipo_registro','Presentacion','Casa3_regla_23mar','Confianza_homologacion']:
        d[c]=d[c].fillna('')
    d['Es_flete']=d.Descripcion_original.str.contains(r'flete|transporte|acarreo|env[ií]o|entrega',case=False,regex=True,na=False) | d.Material_homologado.str.contains('Transporte / flete',case=False,na=False)
    # Mantener presentación comercial; normalizar a kg solo cuando el peso es conocido.
    weightish=d.Material_homologado.str.contains(r'cemento|mortero|repello|fragüe|frague|bondex|pegamento',case=False,regex=True,na=False)
    for idx in d[d.Kg_por_unidad.isna() & weightish].index:
        m=re.search(r'\b(\d+(?:\.\d+)?)\s*(?:kg|kgs|kls)\b',clean(d.at[idx,'Descripcion_original']))
        if m:
            kg=float(m.group(1)); d.at[idx,'Kg_por_unidad']=kg
            if pd.notna(d.at[idx,'Precio_unitario']) and d.at[idx,'Precio_unitario']>0:
                d.at[idx,'Precio_por_kg']=d.at[idx,'Precio_unitario']/kg
    d['Unidad_comercial']=d.apply(commercial_unit,axis=1)
    d['Variante_comparable']=d.apply(comparable_key,axis=1)
    d=add_component(d)
    return d

def add_fiscal(d,tax):
    x=d.copy()
    x['Precio_sin_impuesto']=x.Precio_unitario
    x['Subtotal_sin_impuesto']=x.Total_linea
    x['Impuesto_estimado']=x.Total_linea*tax
    x['Precio_con_impuesto']=x.Precio_unitario*(1+tax)
    x['Total_con_impuesto']=x.Total_linea*(1+tax)
    x['Precio_por_kg_con_impuesto']=x.Precio_por_kg*(1+tax)
    return x

def recipe_base(d,value_col):
    m=d[d.Tipo_registro.isin(RECIPE_TYPES) & ~d.Es_flete].copy()
    keys=['Material_homologado','Familia','Presentacion','Unidad_comercial','Variante_comparable','Componente_fisico','Tipo_registro']
    total=m.groupby(keys,dropna=False,as_index=False).agg(
        Cantidad_total_4_casas=('Cantidad','sum'), Costo_total_4_casas=(value_col,'sum'), Lineas_fuente=('Linea_id','count')
    )
    core=m[m.Casa3_regla_23mar.eq('Sí') & m.Material_homologado.isin(CORE_LABELS)].groupby(keys,dropna=False,as_index=False).agg(
        Cantidad_por_casa=('Cantidad','sum'), Costo_por_casa=(value_col,'sum'), Lineas_confirmadas=('Linea_id','count')
    )
    core=core.merge(total,on=keys,how='left')
    core['Metodo']='Confirmado · última casa > 23/03/2026'
    core['Confianza_receta']='Confirmado'
    core_mats=set(core.Material_homologado)
    other=total[~total.Material_homologado.isin(core_mats)].copy()
    other['Cantidad_por_casa']=other.Cantidad_total_4_casas/4
    other['Costo_por_casa']=other.Costo_total_4_casas/4
    other['Lineas_confirmadas']=0
    other['Metodo']='Estimado · total consolidado ÷ 4'
    other['Confianza_receta']='Estimado'
    # Superblock se conserva visible pero no se trata como block convencional.
    sb=other.Material_homologado.str.contains('Sistema Superblock',case=False,na=False)
    other.loc[sb,'Confianza_receta']='Revisar sistema'
    other.loc[sb,'Metodo']='Revisar · sistema constructivo no comparable a block convencional'
    cols=keys+['Cantidad_total_4_casas','Cantidad_por_casa','Costo_total_4_casas','Costo_por_casa','Lineas_fuente','Lineas_confirmadas','Metodo','Confianza_receta']
    r=pd.concat([core[cols],other[cols]],ignore_index=True)
    rel=m.groupby('Material_homologado').Relevancia.min()
    r['Relevancia']=r.Material_homologado.map(rel).fillna(5)
    return r.sort_values(['Confianza_receta','Relevancia','Costo_por_casa'],ascending=[True,True,False])

def supplier_stats(d,metric,value_col):
    rows=[]
    for p,g in d.groupby('Proveedor'):
        z=g.dropna(subset=[metric]).sort_values('Fecha')
        if z.empty: continue
        first=float(z.iloc[0][metric]); last=float(z.iloc[-1][metric])
        ch=((last-first)/first*100) if first else 0
        tr='Subiendo' if ch>5 else ('Bajando' if ch<-5 else 'Estable')
        rows.append({'Proveedor':p,'MIN':z[metric].min(),'MAX':z[metric].max(),'Ultimo':last,'Total_gastado':g[value_col].sum(),'Compras':g.Factura.nunique(),'Cambio_pct':ch,'Tendencia':tr})
    return pd.DataFrame(rows)

def recipe_cost_trend(d,recipe,price_col):
    # Canasta fija: cantidades de receta no cambian; solo cambian precios históricos.
    x=d[d.Fecha.notna() & d.Cantidad.gt(0) & d[price_col].gt(0)].copy()
    x['Mes']=x.Fecha.dt.to_period('M').dt.to_timestamp()
    keys=['Variante_comparable']
    rr=recipe.groupby(keys,as_index=False).Cantidad_por_casa.sum()
    obs=x.groupby(keys+['Mes'],as_index=False)[price_col].median().rename(columns={price_col:'Precio'})
    if rr.empty or obs.empty: return pd.DataFrame()
    months=pd.DataFrame({'Mes':pd.date_range(obs.Mes.min(),obs.Mes.max(),freq='MS')})
    g=rr[keys].drop_duplicates(); g['_k']=1; months['_k']=1
    grid=g.merge(months,on='_k').drop(columns='_k').merge(obs,on=keys+['Mes'],how='left').sort_values(keys+['Mes'])
    grid['Precio_util']=grid.groupby(keys).Precio.ffill()
    grid=grid.merge(rr,on=keys,how='left')
    grid['Costo']=grid.Cantidad_por_casa*grid.Precio_util
    latest=obs.sort_values('Mes').groupby(keys,as_index=False).tail(1).rename(columns={'Precio':'Precio_ref'})
    ref=rr.merge(latest,on=keys,how='inner'); ref['Costo_ref']=ref.Cantidad_por_casa*ref.Precio_ref
    total_ref=ref.Costo_ref.sum()
    covered=grid[grid.Precio_util.notna()].merge(ref[keys+['Costo_ref']],on=keys,how='left').groupby('Mes',as_index=False).Costo_ref.sum()
    out=grid.groupby('Mes',as_index=False).agg(Costo_receta=('Costo','sum'),Grupos=('Precio_util','count')).merge(covered,on='Mes',how='left')
    out['Cobertura_pct']=np.where(total_ref>0,out.Costo_ref/total_ref*100,0)
    valid=out[out.Cobertura_pct>=70]
    base=float(valid.iloc[0].Costo_receta) if len(valid) else np.nan
    out['Indice']=out.Costo_receta/base*100 if pd.notna(base) and base else np.nan
    return out

def stage_for_family(fam):
    f=clean(fam)
    if any(k in f for k in ['cement','agregado','acero','block','mamposter']): return 'Obra gris / estructura'
    if any(k in f for k in ['electric']): return 'Eléctrico'
    if any(k in f for k in ['plomer','sanitaria','potable']): return 'Hidrosanitario'
    if any(k in f for k in ['gypsum','liviano']): return 'Cielos y divisiones'
    if any(k in f for k in ['piso','enchape','ceram']): return 'Pisos y enchapes'
    if any(k in f for k in ['pintura','acabado']): return 'Pintura / acabados'
    if any(k in f for k in ['carpinter','madera','puerta','cerradura']): return 'Carpintería / cierre'
    return 'Otros'

def price_metric_for_material(x,price_view):
    kg_col='Precio_por_kg_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_por_kg'
    unit_col='Precio_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_sin_impuesto'
    if x[kg_col].notna().sum()>=2: return kg_col,'₡/kg'
    return unit_col,'₡/presentación'

def plan_future(d,recipe,value_col,price_view,n_houses,waste):
    rows=[]
    candidates=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].sort_values(['Relevancia','Costo_por_casa'],ascending=[True,False]).head(60)
    for _,r in candidates.iterrows():
        x=d[(d.Variante_comparable.eq(r.Variante_comparable)) & d.Fecha.notna()].copy()
        if x.empty: continue
        metric,unit=price_metric_for_material(x,price_view); x=x[x[metric].gt(0)]
        ss=supplier_stats(x,metric,value_col)
        if ss.empty: continue
        mn,mx=ss.Ultimo.min(),ss.Ultimo.max(); span=max(mx-mn,1)
        ss['Score']=0.58*((ss.Ultimo-mn)/span)+0.27*(ss.Cambio_pct.clip(-30,30)/60+0.5)-0.15*(np.minimum(ss.Compras,5)/5)
        ss=ss.sort_values('Score'); p1=ss.iloc[0]; p2=ss.iloc[1] if len(ss)>1 else None
        target=float(ss.MIN.min()); qty=float(r.Cantidad_por_casa)*(1+waste)*n_houses
        est=qty*float(p1.Ultimo); target_cost=qty*target
        rows.append({
            'Material_homologado':r.Material_homologado,'Familia':r.Familia,'Presentacion':r.Presentacion,'Unidad_comercial':r.Unidad_comercial,'Variante_comparable':r.Variante_comparable,'Cantidad_meta':qty,
            'Proveedor_1':p1.Proveedor,'Precio_actual':p1.Ultimo,'Tendencia':p1.Tendencia,'Cambio_pct':p1.Cambio_pct,
            'Proveedor_2':p2.Proveedor if p2 is not None else '—','Precio_2':p2.Ultimo if p2 is not None else np.nan,
            'Precio_meta':target,'Metrica':unit,'Costo_estimado':est,'Costo_meta':target_cost,'Ahorro_potencial':max(est-target_cost,0),
            'Confianza_receta':r.Confianza_receta,'Metodo':r.Metodo
        })
    return pd.DataFrame(rows)

# ---------------- Sidebar / assumptions ----------------
df0=load_data()
with st.sidebar:
    st.header('⚙️ Supuestos')
    st.markdown("<div class='sourcebox'><b>Receta:</b> 4 casas esencialmente iguales. Regla general = total consolidado ÷ 4.</div>",unsafe_allow_html=True)
    st.markdown("<div class='sourcebox'><b>Excepción confirmada:</b> block, arena, cemento, piedra y varilla posteriores al 23/03/2026 corresponden a la última casa.</div>",unsafe_allow_html=True)
    tax_pct=st.number_input('Impuesto para estimación (%)',min_value=0.0,max_value=30.0,value=13.0,step=0.5)
    price_view=st.radio('Vista monetaria',['Costo final con impuesto','Precio sin impuesto'],index=0)
    st.caption('La base recibida está sin impuesto. El monto con impuesto es una estimación según la tasa seleccionada.')
    waste_pct=st.slider('Margen de seguridad Casas 5/6 (%)',min_value=0,max_value=20,value=7,step=1)
    future=st.radio('Plan futuro',['Casa 5','Casa 6','Casas 5 + 6'],index=2)

tax=tax_pct/100; waste=waste_pct/100; n_future=2 if future=='Casas 5 + 6' else 1
df=add_fiscal(df0,tax)
value_col='Total_con_impuesto' if price_view=='Costo final con impuesto' else 'Subtotal_sin_impuesto'
unit_price_col='Precio_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_sin_impuesto'
df['Valor_analisis']=df[value_col]
recipe=recipe_base(df,value_col)
recipe['Etapa']=recipe.Familia.map(stage_for_family)
trend=recipe_cost_trend(df,recipe,unit_price_col)
freight=df[df.Es_flete & df.Valor_analisis.gt(1)].copy()
services=df[df.Tipo_registro.isin(['Servicio','Material/servicio']) & ~df.Es_flete].copy()

st.markdown("<div class='hero'><div class='eyebrow'>Inteligencia de construcción · V6</div><h1>Construir Mejor</h1><p><b>La receta, el costo y la oportunidad detrás de cada casa.</b><br>Lo aprendido en cuatro viviendas se convierte en una forma más inteligente de comprar y construir las próximas dos.</p></div>",unsafe_allow_html=True)

st.markdown("""
<div class='story-flow'>
  <div class='story-step'><div class='n'>Punto de partida</div><div class='big'>4 casas</div><div class='small'>2.392 líneas históricas que capturan cómo se ha comprado y construido.</div></div>
  <div class='story-step'><div class='n'>Aprendizaje</div><div class='big'>1 receta</div><div class='small'>Cantidades por vivienda, con estructurales confirmados y resto consolidado ÷ 4.</div></div>
  <div class='story-step'><div class='n'>Evolución</div><div class='big'>↓ Costo</div><div class='small'>La misma receta se revaloriza a precios históricos para medir si realmente estamos construyendo más barato.</div></div>
  <div class='story-step'><div class='n'>Siguiente decisión</div><div class='big'>Casas 5 + 6</div><div class='small'>Cuánto comprar, dónde cotizar, qué precio negociar y qué materiales priorizar.</div></div>
</div>
""", unsafe_allow_html=True)

recipe_cost=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].Costo_por_casa.sum()
label_tax='impuesto estimado incluido' if price_view=='Costo final con impuesto' else 'sin impuesto'
st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Costo receta / casa</div><div class='value'>{money(recipe_cost)}</div><div class='sub'>{label_tax}</div></div><div class='kpi'><div class='label'>Grupos de receta</div><div class='value'>{len(recipe):,}</div><div class='sub'>material + presentación</div></div><div class='kpi'><div class='label'>Base histórica</div><div class='value'>4 casas</div><div class='sub'>viviendas esencialmente iguales</div></div><div class='kpi'><div class='label'>Regla 23/03</div><div class='value'>{recipe.Confianza_receta.eq('Confirmado').sum()}</div><div class='sub'>grupos confirmados</div></div></div>",unsafe_allow_html=True)

tab_names=['🎬 Historia','🏠 Receta','📉 Tendencia de costos','🧩 Anatomía','🏪 Proveedores','📈 Precios']
if len(freight): tab_names.append('🚚 Fletes')
tab_names += ['🎯 Casas 5 y 6','🔎 Base maestra']
tabs=st.tabs(tab_names); T=dict(zip(tab_names,tabs))

# ---------------- HISTORIA / PORTADA EJECUTIVA ----------------
with T['🎬 Historia']:
    st.subheader('🎬 De histórico a decisión')
    st.markdown("<div class='story-callout'><div class='headline'>Cuatro casas nos enseñaron qué comprar, cuánto cuesta y dónde está la próxima oportunidad de ahorro.</div>La historia no termina en el gasto histórico: termina en una receta repetible y en mejores decisiones para Casas 5 y 6.</div>",unsafe_allow_html=True)

    story_recipe=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].copy()
    story_cost=story_recipe.Costo_por_casa.sum()
    rt_story=trend[trend.Cobertura_pct>=70].copy()
    story_change=np.nan
    if len(rt_story)>=2 and rt_story.iloc[0].Costo_receta:
        story_change=(rt_story.iloc[-1].Costo_receta/rt_story.iloc[0].Costo_receta-1)*100

    story_plan=plan_future(df,recipe,value_col,price_view,2,waste)
    story_saving=story_plan.Ahorro_potencial.sum() if len(story_plan) else np.nan

    st.markdown(
        f"<div class='kpi-grid'>"
        f"<div class='kpi'><div class='label'>Receta estándar</div><div class='value'>{money(story_cost)}</div><div class='sub'>costo equivalente por casa · {label_tax}</div></div>"
        f"<div class='kpi'><div class='label'>Evolución comparable</div><div class='value'>{pct(story_change)}</div><div class='sub'>misma receta · precios históricos</div></div>"
        f"<div class='kpi'><div class='label'>Base de aprendizaje</div><div class='value'>4 casas</div><div class='sub'>2.392 líneas homologadas</div></div>"
        f"<div class='kpi'><div class='label'>Oportunidad Casas 5+6</div><div class='value'>{money(story_saving)}</div><div class='sub'>vs precio meta de compra</div></div>"
        f"</div>", unsafe_allow_html=True
    )

    sv=st.selectbox(
        'Visualización principal de la historia',
        ['Trayectoria de costo','Waterfall de aprendizaje','Índice base 100','Composición de la receta','Ruta 4 casas → Casas 5+6']
    )

    if sv=='Trayectoria de costo':
        if len(rt_story)>=2:
            fig=px.line(rt_story,x='Mes',y='Costo_receta',markers=True)
            fig.update_traces(line=dict(width=5),marker=dict(size=9))
            fig.update_layout(title='¿Cuánto cuesta construir hoy la misma receta?',yaxis_title='Costo equivalente por casa')
        else:
            fig=go.Figure()
            fig.add_annotation(text='Cobertura histórica insuficiente',showarrow=False)
    elif sv=='Waterfall de aprendizaje':
        if len(rt_story)>=2:
            first=float(rt_story.iloc[0].Costo_receta); last=float(rt_story.iloc[-1].Costo_receta)
            delta=last-first
            fig=go.Figure(go.Waterfall(
                x=['Inicio comparable','Cambio acumulado','Último comparable'],
                measure=['absolute','relative','total'],
                y=[first,delta,last],
                text=[money(first),money(delta),money(last)],
                textposition='outside'
            ))
            fig.update_layout(title='Del costo de referencia al costo comparable más reciente',yaxis_title='Costo por casa')
        else:
            fig=go.Figure(); fig.add_annotation(text='Cobertura histórica insuficiente',showarrow=False)
    elif sv=='Índice base 100':
        if len(rt_story)>=2:
            fig=px.line(rt_story,x='Mes',y='Indice',markers=True)
            fig.add_hline(y=100,line_dash='dot')
            fig.update_layout(title='Índice del costo de construir la misma casa',yaxis_title='Índice base 100')
        else:
            fig=go.Figure(); fig.add_annotation(text='Cobertura histórica insuficiente',showarrow=False)
    elif sv=='Composición de la receta':
        z=story_recipe.groupby('Familia',as_index=False).Costo_por_casa.sum().sort_values('Costo_por_casa',ascending=False)
        fig=px.treemap(z,path=['Familia'],values='Costo_por_casa')
        fig.update_layout(title='¿Dónde se concentra el costo de una casa?')
    else:
        labels=['4 casas históricas','Receta estándar','Costo comparable','Oportunidades de compra','Casas 5 + 6']
        fig=go.Figure(go.Sankey(
            node=dict(label=labels,pad=18,thickness=20),
            link=dict(source=[0,1,2,3],target=[1,2,3,4],value=[4,4,4,4])
        ))
        fig.update_layout(title='Del histórico a la decisión futura')

    fig.update_layout(height=520)
    st.plotly_chart(fig,use_container_width=True)
    explain(
        'La portada conecta el aprendizaje histórico con una receta estable, la evolución del costo de esa misma receta y el plan de compra futuro.',
        'Entender en segundos si estamos construyendo mejor, qué explica el resultado y dónde concentrar la siguiente decisión.'
    )

    st.markdown("### 🧭 La historia en cuatro preguntas")
    c1,c2,c3,c4=st.columns(4)
    with c1:
        st.markdown("<div class='card'><div class='title'>1. ¿Qué necesita una casa?</div><div class='meta'>La pestaña Receta convierte el consolidado histórico en cantidades por vivienda.</div></div>",unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><div class='title'>2. ¿Estamos bajando el costo?</div><div class='meta'>Tendencia revaloriza la misma receta con precios históricos comparables.</div></div>",unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='card'><div class='title'>3. ¿Qué lo explica?</div><div class='meta'>Proveedores y Precios muestran MIN, MAX, gasto y comportamiento de compra.</div></div>",unsafe_allow_html=True)
    with c4:
        st.markdown("<div class='card'><div class='title'>4. ¿Qué hacemos después?</div><div class='meta'>Casas 5 y 6 transforma el aprendizaje en cantidades, proveedor y precio meta.</div></div>",unsafe_allow_html=True)

# ---------------- RECETA ----------------
with T['🏠 Receta']:
    st.subheader('🏠 Receta estándar de una vivienda')
    st.markdown("<div class='sourcebox'><b>Metodología:</b> cantidades y costos del resto de materiales = total histórico de 4 casas ÷ 4. Block, arena, cemento, piedra y varilla usan directamente la última casa confirmada por la regla posterior al 23/03/2026.</div>",unsafe_allow_html=True)
    conf=st.multiselect('Nivel de receta',['Confirmado','Estimado','Revisar sistema'],default=['Confirmado','Estimado'])
    families=st.multiselect('Filtrar familias',sorted(recipe.Familia.unique()))
    q=recipe[recipe.Confianza_receta.isin(conf)].copy()
    if families: q=q[q.Familia.isin(families)]
    rv=st.selectbox('Visualización de la receta',['Treemap familia → material','Sunburst familia → material','Icicle familia → material','Pareto de costo','Barras horizontales por familia'])
    if rv.startswith('Treemap'):
        fig=px.treemap(q,path=['Familia','Material_homologado'],values='Costo_por_casa',hover_data=['Cantidad_por_casa','Presentacion','Confianza_receta','Metodo'])
    elif rv.startswith('Sunburst'):
        fig=px.sunburst(q,path=['Familia','Material_homologado'],values='Costo_por_casa',hover_data=['Cantidad_por_casa','Presentacion','Confianza_receta'])
    elif rv.startswith('Icicle'):
        fig=px.icicle(q,path=['Familia','Material_homologado'],values='Costo_por_casa',hover_data=['Cantidad_por_casa','Presentacion','Confianza_receta'])
    elif rv.startswith('Pareto'):
        z=q.groupby('Material_homologado',as_index=False).Costo_por_casa.sum().sort_values('Costo_por_casa',ascending=False).head(30)
        z['Acum_pct']=z.Costo_por_casa.cumsum()/max(z.Costo_por_casa.sum(),1)*100
        fig=go.Figure([go.Bar(x=z.Material_homologado,y=z.Costo_por_casa,name='Costo'),go.Scatter(x=z.Material_homologado,y=z.Acum_pct,name='% acumulado',yaxis='y2',mode='lines+markers')])
        fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105],title='% acumulado'))
    else:
        z=q.groupby('Familia',as_index=False).Costo_por_casa.sum().sort_values('Costo_por_casa')
        fig=px.bar(z,x='Costo_por_casa',y='Familia',orientation='h',text_auto='.2s')
    fig.update_layout(height=570,title='Composición de la receta por casa')
    st.plotly_chart(fig,use_container_width=True)
    explain('El costo y la cantidad corresponden a una sola vivienda; la presentación se mantiene separada para no mezclar unidades comerciales.','Validar qué materiales forman la casa y concentrar revisión/negociación en los componentes de mayor peso.')
    st.markdown('### ✅ Estructurales confirmados')
    core=recipe[recipe.Confianza_receta.eq('Confirmado')][['Material_homologado','Presentacion','Unidad_comercial','Variante_comparable','Cantidad_por_casa','Costo_por_casa','Metodo']]
    st.dataframe(core.sort_values('Material_homologado'),use_container_width=True,hide_index=True)
    st.markdown('### 🔎 Receta auditable')
    cols=['Material_homologado','Familia','Presentacion','Unidad_comercial','Variante_comparable','Cantidad_total_4_casas','Cantidad_por_casa','Costo_total_4_casas','Costo_por_casa','Confianza_receta','Metodo','Lineas_fuente']
    st.dataframe(q[cols].sort_values(['Confianza_receta','Costo_por_casa'],ascending=[True,False]),use_container_width=True,hide_index=True,height=480)
    st.download_button('⬇️ Descargar receta por casa',recipe[cols].to_csv(index=False).encode('utf-8-sig'),'receta_estandar_por_casa_v6.csv','text/csv')

# ---------------- TENDENCIA ----------------
with T['📉 Tendencia de costos']:
    st.subheader('📉 ¿Está bajando el costo de construir la misma casa?')
    rt=trend[trend.Cobertura_pct>=70].copy()
    if len(rt)>=2:
        first,last=rt.iloc[0],rt.iloc[-1]; change=(last.Costo_receta/first.Costo_receta-1)*100 if first.Costo_receta else np.nan
        mid=rt.iloc[len(rt)//2]
        st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Inicio comparable</div><div class='value'>{money(first.Costo_receta)}</div><div class='sub'>{first.Mes.strftime('%m/%Y')}</div></div><div class='kpi'><div class='label'>Punto medio</div><div class='value'>{money(mid.Costo_receta)}</div><div class='sub'>{mid.Mes.strftime('%m/%Y')}</div></div><div class='kpi'><div class='label'>Último comparable</div><div class='value'>{money(last.Costo_receta)}</div><div class='sub'>{last.Mes.strftime('%m/%Y')}</div></div><div class='kpi'><div class='label'>Cambio acumulado</div><div class='value'>{pct(change)}</div><div class='sub'>misma receta, precios distintos</div></div></div>",unsafe_allow_html=True)
        tv=st.selectbox('Visualización de la tendencia',['Trayectoria conectada','Área de evolución','Índice base 100','Waterfall de cambios','Hitos históricos'])
        if tv=='Trayectoria conectada':
            fig=px.line(rt,x='Mes',y='Costo_receta',markers=True); fig.update_traces(line=dict(width=5),marker=dict(size=10))
        elif tv=='Área de evolución':
            fig=px.area(rt,x='Mes',y='Costo_receta',markers=True)
        elif tv=='Índice base 100':
            fig=px.line(rt,x='Mes',y='Indice',markers=True); fig.add_hline(y=100,line_dash='dot'); fig.update_yaxes(title='Índice de costo')
        elif tv=='Waterfall de cambios':
            z=rt.copy(); vals=[z.iloc[0].Costo_receta]+z.Costo_receta.diff().iloc[1:].tolist(); measures=['absolute']+['relative']*(len(vals)-1)
            fig=go.Figure(go.Waterfall(x=z.Mes.dt.strftime('%m/%Y'),y=vals,measure=measures,connector={'line':{'width':1}})); fig.update_yaxes(title='Cambio en costo')
        else:
            idx=np.unique(np.linspace(0,len(rt)-1,min(5,len(rt)),dtype=int)); z=rt.iloc[idx]
            fig=px.bar(z,x=z.Mes.dt.strftime('%m/%Y'),y='Costo_receta',text_auto='.3s'); fig.update_xaxes(title='Hitos comparables')
        fig.update_layout(height=530,title='Costo equivalente de una receta fija a precios históricos')
        st.plotly_chart(fig,use_container_width=True)
        explain('Las cantidades de una casa permanecen fijas. Solo cambian los precios históricos; por eso la pendiente representa inflación/ahorro real de compra sobre la misma canasta.','Comprobar si el costo de una vivienda comparable está disminuyendo y cuantificar la mejora sin inventar una asignación de facturas a Casa 1–4.')
        st.caption(f"Cobertura del último período: {last.Cobertura_pct:.0f}% de la canasta de referencia. Se ocultan meses con cobertura menor al 70%.")
    else:
        st.warning('No hay suficientes meses con cobertura comparable para construir la tendencia de costo.')

# ---------------- ANATOMIA ----------------
with T['🧩 Anatomía']:
    st.subheader('🧩 Anatomía física y validación de la receta')
    st.markdown("<div class='sourcebox'><b>Referencia física por casa:</b> 2 habitaciones · 1 baño completo · 1 medio baño · 2 inodoros · 2 lavamanos · 1 ducha · 3 muebles de melamina · 3 ventanas superiores · 1 puerta principal · 1 puerta de servicio/baño · 1 puerta de patio de 3 paneles · 1 cubierta frontal de policarbonato.</div>",unsafe_allow_html=True)
    comp=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].groupby('Componente_fisico',as_index=False).agg(Costo=('Costo_por_casa','sum'),Materiales=('Material_homologado','nunique'),Cantidad=('Cantidad_por_casa','sum'))
    av=st.selectbox('Visualización de componentes',['Treemap de componentes','Sunburst componente → familia','Icicle componente → familia','Barras de costo por componente','Pareto de componentes'])
    if av=='Treemap de componentes': fig=px.treemap(comp,path=['Componente_fisico'],values='Costo',hover_data=['Materiales'])
    elif av.startswith('Sunburst'):
        z=recipe.groupby(['Componente_fisico','Familia'],as_index=False).Costo_por_casa.sum(); fig=px.sunburst(z,path=['Componente_fisico','Familia'],values='Costo_por_casa')
    elif av.startswith('Icicle'):
        z=recipe.groupby(['Componente_fisico','Familia'],as_index=False).Costo_por_casa.sum(); fig=px.icicle(z,path=['Componente_fisico','Familia'],values='Costo_por_casa')
    elif av.startswith('Barras'):
        z=comp.sort_values('Costo'); fig=px.bar(z,x='Costo',y='Componente_fisico',orientation='h',text_auto='.2s')
    else:
        z=comp.sort_values('Costo',ascending=False); z['Acum']=z.Costo.cumsum()/max(z.Costo.sum(),1)*100
        fig=go.Figure([go.Bar(x=z.Componente_fisico,y=z.Costo),go.Scatter(x=z.Componente_fisico,y=z.Acum,yaxis='y2',mode='lines+markers')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
    fig.update_layout(height=540,title='Costo de receta por componente físico')
    st.plotly_chart(fig,use_container_width=True)
    explain('Agrupa la receta por función física dentro de la vivienda, no solamente por proveedor o familia contable.','Detectar componentes faltantes o desproporcionados antes de utilizar la receta para Casas 5 y 6.')
    targets=pd.DataFrame([
        ['Habitaciones',2,'Referencia de diseño'],['Inodoros',2,'Referencia de diseño'],['Lavamanos',2,'Referencia de diseño'],['Duchas',1,'Referencia de diseño'],['Muebles de melamina',3,'2 dormitorios + cocina'],['Ventanas superiores',3,'2 dormitorios + baño'],['Puerta principal',1,'Referencia de diseño'],['Puerta servicio/medio baño',1,'Referencia de diseño'],['Puerta patio 3 paneles',1,'Referencia de diseño'],['Cubierta frontal policarbonato',1,'Referencia de diseño']
    ],columns=['Elemento','Cantidad esperada por casa','Validación'])
    st.dataframe(targets,use_container_width=True,hide_index=True)
    if len(services):
        st.caption('Servicios (por ejemplo cortes) se mantienen fuera de la cantidad física de materiales y se analizan como costo complementario, para no contaminar la receta material.')

# ---------------- PROVEEDORES ----------------
with T['🏪 Proveedores']:
    st.subheader('🏪 Material × proveedor · MIN, MAX y total gastado')
    mats=sorted(df[df.Tipo_registro.isin(RECIPE_TYPES)].Material_homologado.unique())
    mat=st.selectbox('Material',mats)
    variants=sorted(df[df.Material_homologado.eq(mat)].Variante_comparable.unique()); variant=st.selectbox('Producto / variante comparable',variants)
    x=df[(df.Variante_comparable.eq(variant))&df.Fecha.notna()].copy(); presentation=x.Presentacion.iloc[0] if len(x) else '—'
    metric,metric_label=price_metric_for_material(x,price_view); x=x[x[metric].gt(0)]
    ss=supplier_stats(x,metric,value_col)
    if ss.empty: st.info('Sin suficientes compras comparables para este material/presentación.')
    else:
        pv=st.selectbox('Visualización de proveedores',['Rango MIN–MAX (dumbbell)','Heatmap MIN / MAX / total','Ranking por último precio','Barras de total gastado','Bullet de negociación'])
        if pv.startswith('Rango'):
            z=ss.sort_values('Ultimo'); fig=go.Figure()
            for _,r in z.iterrows(): fig.add_trace(go.Scatter(x=[r.MIN,r.MAX],y=[r.Proveedor,r.Proveedor],mode='lines+markers',showlegend=False,hovertemplate=f"{r.Proveedor}<br>MIN %{{x:,.0f}} / MAX<extra></extra>"))
            fig.update_xaxes(title=metric_label)
        elif pv.startswith('Heatmap'):
            z=ss.set_index('Proveedor')[['MIN','MAX','Total_gastado']]; fig=px.imshow(z,aspect='auto',text_auto='.2s',labels=dict(color='Valor'))
        elif pv.startswith('Ranking'):
            z=ss.sort_values('Ultimo',ascending=False); fig=px.bar(z,x='Ultimo',y='Proveedor',orientation='h',text_auto='.3s'); fig.update_xaxes(title=metric_label)
        elif pv.startswith('Barras'):
            z=ss.sort_values('Total_gastado'); fig=px.bar(z,x='Total_gastado',y='Proveedor',orientation='h',text_auto='.2s')
        else:
            z=ss.sort_values('Ultimo'); target=float(ss.MIN.min()); fig=go.Figure()
            for i,(_,r) in enumerate(z.iterrows()):
                fig.add_trace(go.Indicator(mode='number+gauge',value=r.Ultimo,title={'text':r.Proveedor},domain={'row':i,'column':0},gauge={'shape':'bullet','axis':{'range':[0,max(ss.MAX.max(),1)]},'threshold':{'value':target}}))
            fig.update_layout(grid={'rows':len(z),'columns':1,'pattern':'independent'},height=max(320,125*len(z)))
        fig.update_layout(height=max(500,fig.layout.height or 500),title=f'{mat} · {presentation}')
        st.plotly_chart(fig,use_container_width=True)
        explain('MIN y MAX muestran el rango real; total gastado muestra relación histórica; último precio permite ubicar la cotización actual dentro de ese rango.','Elegir a quién cotizar y cuál es un objetivo de negociación defendible sin usar promedios que oculten extremos.')
        st.dataframe(ss.sort_values('Ultimo'),use_container_width=True,hide_index=True)

# ---------------- PRECIOS ----------------
with T['📈 Precios']:
    st.subheader('📈 Evolución histórica de precio')
    mats=sorted(df[df.Tipo_registro.isin(RECIPE_TYPES)].Material_homologado.unique()); matp=st.selectbox('Material para tendencia',mats,key='mat_price')
    variants=sorted(df[df.Material_homologado.eq(matp)].Variante_comparable.unique()); variantp=st.selectbox('Producto / variante comparable',variants,key='variant_price')
    x=df[(df.Variante_comparable.eq(variantp))&df.Fecha.notna()].copy(); pp=x.Presentacion.iloc[0] if len(x) else '—'; metric,metric_label=price_metric_for_material(x,price_view); x=x[x[metric].gt(0)].sort_values('Fecha')
    if x.empty: st.info('Sin precios comparables.')
    else:
        ev=st.selectbox('Visualización de evolución',['Líneas por proveedor','Área por proveedor','Índice base 100 por proveedor','Rango MIN–MAX mensual','Escalones de último precio'])
        if ev=='Líneas por proveedor': fig=px.line(x,x='Fecha',y=metric,color='Proveedor',markers=True)
        elif ev=='Área por proveedor': fig=px.area(x,x='Fecha',y=metric,color='Proveedor',facet_row='Proveedor',height=max(500,180*x.Proveedor.nunique()))
        elif ev.startswith('Índice'):
            z=x.copy(); z['Indice']=z.groupby('Proveedor')[metric].transform(lambda s:s/s.iloc[0]*100 if len(s) and s.iloc[0] else np.nan); fig=px.line(z,x='Fecha',y='Indice',color='Proveedor',markers=True); fig.add_hline(y=100,line_dash='dot')
        elif ev.startswith('Rango'):
            z=x.assign(Mes=x.Fecha.dt.to_period('M').dt.to_timestamp()).groupby('Mes')[metric].agg(['min','max']).reset_index(); fig=go.Figure(); fig.add_trace(go.Scatter(x=z.Mes,y=z['max'],mode='lines',name='MAX')); fig.add_trace(go.Scatter(x=z.Mes,y=z['min'],mode='lines',name='MIN',fill='tonexty'))
        else:
            z=x.sort_values('Fecha'); fig=go.Figure()
            for p,g in z.groupby('Proveedor'): fig.add_trace(go.Scatter(x=g.Fecha,y=g[metric],mode='lines+markers',line_shape='hv',name=p))
        fig.update_layout(height=540,title=f'{matp} · {pp}',yaxis_title=metric_label)
        st.plotly_chart(fig,use_container_width=True)
        explain('Todas las series comparan la misma presentación; cuando existe peso conocido se puede comparar por kg para evitar confundir bolsas/sacos de tamaños distintos.','Decidir si conviene comprar pronto, esperar, cambiar proveedor o fijar un precio objetivo.')

# ---------------- FLETES ----------------
if '🚚 Fletes' in T:
    with T['🚚 Fletes']:
        st.subheader('🚚 Transporte y costo puesto en obra')
        fv=st.selectbox('Visualización de fletes',['Barras por proveedor','Treemap proveedor → cargo','Sunburst proveedor → cargo','Waterfall cronológico','Área acumulada'])
        if fv.startswith('Barras'):
            z=freight.groupby('Proveedor',as_index=False).Valor_analisis.sum().sort_values('Valor_analisis'); fig=px.bar(z,x='Valor_analisis',y='Proveedor',orientation='h',text_auto='.2s')
        elif fv.startswith('Treemap'): fig=px.treemap(freight,path=['Proveedor','Descripcion_original'],values='Valor_analisis')
        elif fv.startswith('Sunburst'): fig=px.sunburst(freight,path=['Proveedor','Descripcion_original'],values='Valor_analisis')
        elif fv.startswith('Waterfall'):
            z=freight.sort_values('Fecha'); fig=go.Figure(go.Waterfall(x=z.Fecha.astype(str),y=z.Valor_analisis,measure=['relative']*len(z)))
        else:
            z=freight.sort_values('Fecha').copy(); z['Acumulado']=z.Valor_analisis.cumsum(); fig=px.area(z,x='Fecha',y='Acumulado')
        fig.update_layout(height=520,title='Fletes identificados')
        st.plotly_chart(fig,use_container_width=True)
        explain('Se muestran únicamente cargos reales de transporte mayores a ₡1; no se mezclan con la cantidad física de materiales.','Evaluar costo puesto en obra, consolidación de viajes y proveedores con mayor carga logística.')
        st.metric('Flete histórico identificado',money(freight.Valor_analisis.sum()))

# ---------------- FUTURO ----------------
with T['🎯 Casas 5 y 6']:
    st.subheader(f'🎯 Plan de compra · {future}')
    plan=plan_future(df,recipe,value_col,price_view,n_future,waste)
    if plan.empty: st.warning('No hay suficiente información comparable para generar el plan.')
    else:
        total_plan=plan.Costo_estimado.sum(); saving=plan.Ahorro_potencial.sum(); rising=(plan.Tendencia=='Subiendo').sum()
        st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Presupuesto de referencia</div><div class='value'>{money(total_plan)}</div></div><div class='kpi'><div class='label'>Oportunidad vs meta</div><div class='value'>{money(saving)}</div></div><div class='kpi'><div class='label'>Materiales al alza</div><div class='value'>{rising}</div></div><div class='kpi'><div class='label'>Margen de seguridad</div><div class='value'>{waste_pct}%</div></div></div>",unsafe_allow_html=True)
        fv=st.selectbox('Visualización del plan',['Ranking de ahorro potencial','Waterfall de oportunidad','Heatmap material × proveedor','Sankey material → proveedor','Barras de prioridad de compra'])
        if fv.startswith('Ranking'):
            z=plan.sort_values('Ahorro_potencial').tail(30); fig=px.bar(z,x='Ahorro_potencial',y='Material_homologado',orientation='h',text_auto='.2s',hover_data=['Proveedor_1','Precio_actual','Precio_meta'])
        elif fv.startswith('Waterfall'):
            z=plan.sort_values('Ahorro_potencial',ascending=False).head(20); fig=go.Figure(go.Waterfall(x=z.Material_homologado,y=-z.Ahorro_potencial,measure=['relative']*len(z))); fig.update_yaxes(title='Reducción potencial')
        elif fv.startswith('Heatmap'):
            z=plan.pivot_table(index='Material_homologado',columns='Proveedor_1',values='Costo_estimado',aggfunc='sum',fill_value=0); fig=px.imshow(z,aspect='auto',text_auto='.2s')
        elif fv.startswith('Sankey'):
            z=plan.sort_values('Costo_estimado',ascending=False).head(25); mats=z.Material_homologado.tolist(); provs=list(dict.fromkeys(z.Proveedor_1.tolist())); labels=mats+provs; src=[];tgt=[];val=[]
            for _,r in z.iterrows(): src.append(labels.index(r.Material_homologado));tgt.append(labels.index(r.Proveedor_1));val.append(max(float(r.Costo_estimado),1))
            fig=go.Figure(go.Sankey(node=dict(label=labels,pad=12,thickness=16),link=dict(source=src,target=tgt,value=val)))
        else:
            z=plan.copy(); z['Prioridad']=np.where(z.Tendencia.eq('Subiendo'),3,np.where(z.Tendencia.eq('Estable'),2,1))*np.log1p(z.Costo_estimado); z=z.sort_values('Prioridad').tail(30); fig=px.bar(z,x='Prioridad',y='Material_homologado',orientation='h',hover_data=['Proveedor_1','Tendencia','Cantidad_meta','Precio_meta'])
        fig.update_layout(height=600,title='Plan priorizado de compra')
        st.plotly_chart(fig,use_container_width=True)
        explain('La receta fija las cantidades; el precio reciente, tendencia, MIN–MAX y recurrencia determinan proveedor recomendado, meta y prioridad.','Ordenar cotizaciones de Casas 5–6 y enfocar la negociación donde existe mayor impacto económico.')
        material=st.selectbox('Detalle de material',plan.Material_homologado.tolist())
        r=plan[plan.Material_homologado.eq(material)].iloc[0]
        c1,c2,c3=st.columns(3)
        c1.metric('Cantidad objetivo',f"{r.Cantidad_meta:,.1f} {r.Presentacion}")
        c2.metric('🥇 Proveedor recomendado',r.Proveedor_1)
        c3.metric('🎯 Precio meta',money(r.Precio_meta))
        st.markdown(f"<div class='explain'><b>Último precio:</b> {money(r.Precio_actual)} {r.Metrica} · <b>Tendencia:</b> {r.Tendencia} ({pct(r.Cambio_pct)}) · <b>Alternativa:</b> {r.Proveedor_2}.<br><b>Origen de cantidad:</b> {r.Metodo}.</div>",unsafe_allow_html=True)
        st.download_button('⬇️ Descargar plan Casas 5–6',plan.to_csv(index=False).encode('utf-8-sig'),'plan_compras_casas_5_6_v6.csv','text/csv')

# ---------------- EXPLORADOR ----------------
with T['🔎 Base maestra']:
    st.subheader('🔎 Base maestra · auditoría')
    c1,c2,c3,c4=st.columns(4); c1.metric('Líneas',f'{len(df):,}'); c2.metric('Materiales',df.Material_homologado.nunique()); c3.metric('Proveedores',df.Proveedor.nunique()); c4.metric('Regla 23/03',int(df.Casa3_regla_23mar.eq('Sí').sum()))
    bv=st.selectbox('Visualización resumen de la base',['Treemap por familia','Sunburst familia → proveedor','Barras por tipo de registro','Pareto de proveedores','Heatmap familia × tipo'])
    if bv.startswith('Treemap'): fig=px.treemap(df,path=['Familia'],values='Valor_analisis')
    elif bv.startswith('Sunburst'): fig=px.sunburst(df,path=['Familia','Proveedor'],values='Valor_analisis')
    elif bv.startswith('Barras'):
        z=df.groupby('Tipo_registro',as_index=False).Valor_analisis.sum().sort_values('Valor_analisis'); fig=px.bar(z,x='Valor_analisis',y='Tipo_registro',orientation='h',text_auto='.2s')
    elif bv.startswith('Pareto'):
        z=df.groupby('Proveedor',as_index=False).Valor_analisis.sum().sort_values('Valor_analisis',ascending=False).head(25); z['Acum']=z.Valor_analisis.cumsum()/max(z.Valor_analisis.sum(),1)*100; fig=go.Figure([go.Bar(x=z.Proveedor,y=z.Valor_analisis),go.Scatter(x=z.Proveedor,y=z.Acum,yaxis='y2',mode='lines+markers')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
    else:
        z=df.pivot_table(index='Familia',columns='Tipo_registro',values='Valor_analisis',aggfunc='sum',fill_value=0); fig=px.imshow(z,aspect='auto')
    fig.update_layout(height=520,title='Resumen de la base homologada')
    st.plotly_chart(fig,use_container_width=True)
    explain('Esta visualización resume el universo completo, mientras la tabla permite auditar cada línea fuente.','Localizar concentraciones, anomalías o clasificaciones que deban corregirse antes de afectar la receta.')
    search=st.text_input('🔍 Buscar descripción, material, proveedor o factura')
    a,b,c=st.columns(3)
    fam=a.multiselect('Familia',sorted(df.Familia.unique())); prov=b.multiselect('Proveedor',sorted(df.Proveedor.unique())); typ=c.multiselect('Tipo',sorted(df.Tipo_registro.unique()))
    z=df.copy()
    if fam: z=z[z.Familia.isin(fam)]
    if prov: z=z[z.Proveedor.isin(prov)]
    if typ: z=z[z.Tipo_registro.isin(typ)]
    if search:
        q=re.escape(search); z=z[z.Material_homologado.str.contains(q,case=False,regex=True,na=False)|z.Descripcion_original.str.contains(q,case=False,regex=True,na=False)|z.Proveedor.str.contains(q,case=False,regex=True,na=False)|z.Factura.astype(str).str.contains(q,case=False,regex=True,na=False)]
    cols=['Fecha','Proveedor','Factura','Material_homologado','Descripcion_original','Cantidad','Presentacion','Unidad_comercial','Variante_comparable','Precio_sin_impuesto','Total_con_impuesto','Precio_por_kg','Familia','Tipo_registro','Componente_fisico','Confianza_homologacion','Casa3_regla_23mar']
    st.dataframe(z[cols].sort_values('Fecha',ascending=False),use_container_width=True,hide_index=True,height=520)
    st.download_button('⬇️ Descargar selección',z.to_csv(index=False).encode('utf-8-sig'),'base_maestra_filtrada_v6.csv','text/csv')

st.divider()
st.caption('Construir Mejor · V6 · 4 casas → 1 receta → evolución de costo → oportunidades → Casas 5 y 6 · receta total÷4 + excepción estructural 23/03 · múltiples visualizaciones en cada análisis.')
