from pathlib import Path
import math, re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def house_cost_history(df, value_col, house_area):
    """Costo registrado por ciclo de vivienda.
    La fecha visible del gráfico corresponde al cierre del ciclo.
    """
    specs = [
        ('Casa 1', 'Superbloque', pd.Timestamp('2024-11-01'), pd.Timestamp('2025-03-22')),
        ('Casa 2', 'Superbloque', pd.Timestamp('2025-03-23'), pd.Timestamp('2025-08-31')),
        ('Casa 3', 'Superbloque', pd.Timestamp('2025-09-01'), pd.Timestamp('2026-03-22')),
        ('Casa 4', 'Block convencional', pd.Timestamp('2026-03-23'), pd.Timestamp('2026-08-31')),
    ]
    rows = []
    for casa, sistema, ini, fin in specs:
        z = df[df['Fecha'].between(ini, fin, inclusive='both')].copy()
        costo = float(pd.to_numeric(z[value_col], errors='coerce').fillna(0).sum())
        rows.append({
            'Casa': casa,
            'Sistema': sistema,
            'Inicio': ini,
            'Fin': fin,
            'Fecha_grafico': fin,
            'Costo': costo,
            'Costo_m2': costo / house_area if house_area else np.nan,
            'Lineas': len(z),
        })
    h = pd.DataFrame(rows)
    h['Delta'] = h['Costo'].diff()
    h['Delta_pct'] = h['Costo'].pct_change() * 100
    first = float(h.iloc[0]['Costo']) if len(h) else 0
    h['Indice'] = h['Costo'] / first * 100 if first else np.nan
    return h


st.set_page_config(page_title="Construir Mejor · V7 MASTER DECISION", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")
BASE = Path(__file__).with_name("base_maestra_homologada_2392.csv")
RECIPE_TYPES = ["Material permanente", "Material/consumible", "Consumible de obra"]
CORE_LABELS = {
    "Cemento gris 50 kg", "Arena", "Piedra / agregado", "Varilla #3", "Varilla #4",
    "Block concreto 12x20x40", "Block concreto 15x20x40"
}
HOUSE_AREA_M2 = 100.0

# Benchmark oficial INEC Costa Rica · IPCONS base febrero 2025.
# Serie 2026 verificada contra publicaciones mensuales oficiales disponibles a julio 2026.
INEC_BUILDINGS_2026 = pd.DataFrame({
    "Mes": pd.to_datetime(["2026-01-01","2026-02-01","2026-03-01","2026-04-01","2026-05-01","2026-06-01","2026-07-01"]),
    "INEC_Edificios": [96.871,96.638,96.422,96.481,97.109,97.882,98.037],
    "INEC_Vivienda_social": [99.691,99.655,99.417,100.153,101.399,102.119,102.311],
})
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
def explain(read, decision, insight=None):
    shown = insight if insight else decision
    st.markdown(
        f"<div class='explain'>"
        f"<b>📖 ¿Cómo leerlo?</b> {read}<br>"
        f"<b>🔎 ¿Qué nos muestra?</b> {shown}<br>"
        f"<b>🎯 Decisión recomendada</b> {decision}"
        f"</div>", unsafe_allow_html=True
    )
def clean(s):
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9/#.xáéíóúñ\s]+"," ",str(s).lower())).strip()

def extract_size(desc):
    s=clean(desc)
    patterns=[
        r'\b\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?(?:\s*x\s*\d+(?:\.\d+)?)?\s*(?:cm|mm|m)?\b',
        r'\b\d+\s+\d+/\d+\b',r'\b\d+/\d+\b',
        r'\b\d+(?:\.\d+)?\s*mm\b',r'\b\d+(?:\.\d+)?\s*cm\b',r'\b#\s*\d+\b'
    ]
    for pat in patterns:
        m=re.search(pat,s)
        if m: return re.sub(r'\s+','',m.group(0))
    return ''

def commercial_unit(row):
    d=clean(row.get('Descripcion_original','')); mat=clean(row.get('Material_homologado','')); prov=clean(row.get('Proveedor','')); pres=str(row.get('Presentacion','') or '')
    if pd.notna(row.get('Kg_por_unidad')) and float(row.get('Kg_por_unidad') or 0)>0: return pres or 'Unidad con peso conocido'
    for word,label in [('paquete','Paquete'),('bolsa','Bolsa'),('caja','Caja'),('rollo','Rollo'),('juego','Juego'),('set','Set')]:
        if word in d: return label
    if 'clavo' in mat and 'epa' in prov: return 'Paquete/bolsa EPA'
    return pres if pres and pres!='nan' else 'Unidad comercial'

def product_subtype(row):
    d=clean(row.get('Descripcion_original','')); mat=clean(row.get('Material_homologado',''))
    if 'cerrajer' in mat:
        if 'bisag' in d: return 'Bisagra'
        if 'cerradura' in d: return 'Cerradura'
        if 'cerroj' in d: return 'Cerrojo'
    if 'melamina' in mat:
        if 'corte melamina' in d: return 'Servicio de corte'
        if 'disco' in d and 'sierra' in d: return 'Herramienta de corte'
        return 'Lámina melamina'
    return ''

def comparable_key(row):
    mat=str(row.get('Material_homologado','')); size=extract_size(row.get('Descripcion_original','')); unit=str(row.get('Unidad_comercial',''))
    sub=product_subtype(row)
    parts=[mat]
    if sub: parts.append(sub)
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

    # Cost Breakdown Structure (CBS): lectura por sistema de la vivienda.
    x['Sistema_costo']='Otros / soporte de obra'
    x.loc[txt.str.contains(r'cemento|arena|piedra|block|varilla|acero refuerzo|malla elect|concreto',regex=True),'Sistema_costo']='Estructura / obra gris'
    x.loc[txt.str.contains(r'policarbon|cubierta|techo|canoa|cumbrera|botagua',regex=True),'Sistema_costo']='Cubiertas'
    x.loc[txt.str.contains(r'pvc|tuber|sifon|hidro|plomer|llave paso|válvula|valvula',regex=True),'Sistema_costo']='Instalación hidrosanitaria'
    x.loc[txt.str.contains(r'cable|conduit|tomacorr|interruptor|breaker|electr|luminaria|bombillo',regex=True),'Sistema_costo']='Instalación eléctrica'
    x.loc[txt.str.contains(r'inodoro|lavaman|ducha|sanitari|grifer',regex=True),'Sistema_costo']='Baños / sanitarios'
    x.loc[txt.str.contains(r'porcel|ceram|piso|enchape|fragüe|frague|bondex',regex=True),'Sistema_costo']='Pisos / revestimientos'
    x.loc[txt.str.contains(r'pintura|sellador|esmalte|brocha|rodillo|masilla',regex=True),'Sistema_costo']='Pintura / acabados'
    x.loc[txt.str.contains(r'puerta|cerradura|marco puerta|tope puerta|ventana|vidrio|espejo',regex=True),'Sistema_costo']='Puertas / ventanas'
    x.loc[txt.str.contains(r'melamin|mueble|closet|gabinet|tapacanto|corredera',regex=True),'Sistema_costo']='Carpintería / melamina'
    x.loc[txt.str.contains(r'gypsum|fibrocement|cielo|stud|track',regex=True),'Sistema_costo']='Divisiones / cielos'
    return x

@st.cache_data(show_spinner=False)
def load_data():
    d=pd.read_csv(BASE)
    d['Fecha']=pd.to_datetime(d['Fecha'],errors='coerce')
    for c in ['Cantidad','Precio_unitario','Total_linea','Kg_por_unidad','Precio_por_kg','Relevancia']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    for c in ['Proveedor','Factura','Descripcion_original','Material_homologado','Familia','Tipo_registro','Presentacion','Casa3_regla_23mar','Confianza_homologacion']:
        d[c]=d[c].fillna('')

    # V7 · Reglas de calidad detectadas ANTES de construir receta/tendencias.
    # Se conserva la descripción original; solo se corrige la clasificación analítica.
    d['Regla_calidad_v7']=''
    cut_mel=d.Descripcion_original.str.contains(r'corte\s+melamina',case=False,regex=True,na=False)
    d.loc[cut_mel,'Regla_calidad_v7']='Servicio de corte de melamina excluido de receta física'
    d.loc[cut_mel,'Material_homologado']='Servicio corte melamina'
    d.loc[cut_mel,'Familia']='Servicios de carpintería'
    d.loc[cut_mel,'Tipo_registro']='Servicio'

    saw_mel=d.Descripcion_original.str.contains(r'disco\s+sierra.*melamina',case=False,regex=True,na=False)
    d.loc[saw_mel,'Regla_calidad_v7']='Disco de sierra reclasificado como herramienta'
    d.loc[saw_mel,'Material_homologado']='Disco sierra para melamina'
    d.loc[saw_mel,'Familia']='Herramientas'
    d.loc[saw_mel,'Tipo_registro']='Herramienta/equipo'

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
    keys=['Material_homologado','Familia','Presentacion','Unidad_comercial','Variante_comparable','Componente_fisico','Sistema_costo','Tipo_registro']
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
    """
    Canasta fija depurada:
    - excluye grupos marcados como 'Revisar sistema'
    - separa variantes comerciales comparables
    - usa último precio conocido por variante
    - mide cobertura económica respecto a la canasta de referencia
    - solo considera comparable la trayectoria >=95% de cobertura
    """
    r=recipe.copy()
    if 'Confianza_receta' in r.columns:
        r=r[~r.Confianza_receta.eq('Revisar sistema')].copy()

    x=d[d.Fecha.notna() & d.Cantidad.gt(0) & d[price_col].gt(0)].copy()
    x['Mes']=x.Fecha.dt.to_period('M').dt.to_timestamp()
    keys=['Variante_comparable']
    rr=r.groupby(keys,as_index=False).Cantidad_por_casa.sum()
    obs=x.groupby(keys+['Mes'],as_index=False)[price_col].median().rename(columns={price_col:'Precio'})
    if rr.empty or obs.empty:
        return pd.DataFrame()

    months=pd.DataFrame({'Mes':pd.date_range(obs.Mes.min(),obs.Mes.max(),freq='MS')})
    g=rr[keys].drop_duplicates(); g['_k']=1; months['_k']=1
    grid=(g.merge(months,on='_k').drop(columns='_k')
          .merge(obs,on=keys+['Mes'],how='left')
          .sort_values(keys+['Mes']))
    grid['Precio_util']=grid.groupby(keys).Precio.ffill()
    grid['Mes_ultimo_precio']=grid['Mes'].where(grid.Precio.notna())
    grid['Mes_ultimo_precio']=grid.groupby(keys).Mes_ultimo_precio.ffill()
    grid['Edad_precio_dias']=(grid.Mes-grid.Mes_ultimo_precio).dt.days

    grid=grid.merge(rr,on=keys,how='left')
    grid['Costo']=grid.Cantidad_por_casa*grid.Precio_util

    # La referencia se construye con el último precio disponible de cada SKU.
    latest=(obs.sort_values('Mes').groupby(keys,as_index=False).tail(1)
            .rename(columns={'Precio':'Precio_ref'}))
    ref=rr.merge(latest,on=keys,how='inner')
    ref['Costo_ref']=ref.Cantidad_por_casa*ref.Precio_ref
    total_ref=ref.Costo_ref.sum()

    covered=(grid[grid.Precio_util.notna()]
             .merge(ref[keys+['Costo_ref']],on=keys,how='left')
             .groupby('Mes',as_index=False).Costo_ref.sum())

    fresh=(grid[grid.Precio_util.notna() & grid.Edad_precio_dias.le(180)]
           .merge(ref[keys+['Costo_ref']],on=keys,how='left')
           .groupby('Mes',as_index=False).Costo_ref.sum()
           .rename(columns={'Costo_ref':'Costo_ref_fresco'}))

    out=(grid.groupby('Mes',as_index=False)
         .agg(Costo_receta=('Costo','sum'),Grupos=('Precio_util','count'))
         .merge(covered,on='Mes',how='left')
         .merge(fresh,on='Mes',how='left'))
    out['Cobertura_pct']=np.where(total_ref>0,out.Costo_ref/total_ref*100,0)
    out['Cobertura_fresca_pct']=np.where(total_ref>0,out.Costo_ref_fresco.fillna(0)/total_ref*100,0)
    out['Comparable']=out.Cobertura_pct>=95
    valid=out[out.Comparable]
    base=float(valid.iloc[0].Costo_receta) if len(valid) else np.nan
    out['Indice']=out.Costo_receta/base*100 if pd.notna(base) and base else np.nan
    out['Cambio_mensual_pct']=out.Costo_receta.pct_change()*100
    return out

def trend_driver_detail(d,recipe,price_col,month):
    """Explica el cambio mensual de la misma canasta fija, variante por variante."""
    r=recipe.copy()
    if 'Confianza_receta' in r.columns:
        r=r[~r.Confianza_receta.eq('Revisar sistema')].copy()
    rr=r.groupby('Variante_comparable',as_index=False).agg(
        Cantidad_por_casa=('Cantidad_por_casa','sum'),
        Material=('Material_homologado','first'),
        Familia=('Familia','first'),
        Sistema=('Sistema_costo','first')
    )
    x=d[d.Fecha.notna() & d.Cantidad.gt(0) & d[price_col].gt(0)].copy()
    x['Mes']=x.Fecha.dt.to_period('M').dt.to_timestamp()
    obs=x.groupby(['Variante_comparable','Mes'],as_index=False)[price_col].median().rename(columns={price_col:'Precio'})
    if obs.empty: return pd.DataFrame()
    months=pd.DataFrame({'Mes':pd.date_range(obs.Mes.min(),obs.Mes.max(),freq='MS')})
    g=rr[['Variante_comparable']].drop_duplicates(); g['_k']=1; months['_k']=1
    grid=(g.merge(months,on='_k').drop(columns='_k')
          .merge(obs,on=['Variante_comparable','Mes'],how='left')
          .sort_values(['Variante_comparable','Mes']))
    grid['Precio_util']=grid.groupby('Variante_comparable').Precio.ffill()
    grid=grid.merge(rr,on='Variante_comparable',how='left')
    grid['Costo']=grid.Cantidad_por_casa*grid.Precio_util
    prev=pd.Timestamp(month)-pd.offsets.MonthBegin(1)
    a=grid[grid.Mes.eq(prev)][['Variante_comparable','Costo']].rename(columns={'Costo':'Costo_anterior'})
    b=grid[grid.Mes.eq(pd.Timestamp(month))][['Variante_comparable','Costo']].rename(columns={'Costo':'Costo_actual'})
    z=rr.merge(a,on='Variante_comparable',how='left').merge(b,on='Variante_comparable',how='left')
    z[['Costo_anterior','Costo_actual']]=z[['Costo_anterior','Costo_actual']].fillna(0)
    z['Impacto']=z.Costo_actual-z.Costo_anterior
    z['Impacto_abs']=z.Impacto.abs()
    return z.sort_values('Impacto_abs',ascending=False)


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


def recipe_quality(d, recipe):
    r=recipe.copy()
    included=r[~r.Confianza_receta.eq('Revisar sistema')]
    cost=included.Costo_por_casa.sum()
    confirmed=included.loc[included.Confianza_receta.eq('Confirmado'),'Costo_por_casa'].sum()
    estimated=included.loc[included.Confianza_receta.eq('Estimado'),'Costo_por_casa'].sum()
    return {
        'Costo_receta':cost,
        'Pct_confirmado': confirmed/cost*100 if cost else 0,
        'Pct_estimado': estimated/cost*100 if cost else 0,
        'Grupos_revisar': int(r.Confianza_receta.eq('Revisar sistema').sum()),
        'Lineas_regla': int(d.Casa3_regla_23mar.eq('Sí').sum()),
    }

def abc_recipe(recipe):
    z=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].copy().sort_values('Costo_por_casa',ascending=False)
    total=max(z.Costo_por_casa.sum(),1)
    z['Participacion_pct']=z.Costo_por_casa/total*100
    z['Acumulado_pct']=z.Participacion_pct.cumsum()
    z['ABC']=np.select([z.Acumulado_pct<=80,z.Acumulado_pct<=95],['A','B'],default='C')
    return z

def should_cost_table(d, recipe, price_view, value_col):
    rows=[]
    kg_col='Precio_por_kg_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_por_kg'
    unit_col='Precio_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_sin_impuesto'
    for _,r in recipe[~recipe.Confianza_receta.eq('Revisar sistema')].iterrows():
        x=d[(d.Variante_comparable.eq(r.Variante_comparable)) & d.Fecha.notna()].copy().sort_values('Fecha')
        metric=kg_col if x[kg_col].notna().sum()>=2 else unit_col
        x=x[x[metric].gt(0)]
        if x.empty: continue
        latest_date=x.Fecha.max()
        recent=x[x.Fecha>=latest_date-pd.Timedelta(days=180)]
        if recent.empty: recent=x
        current=float(x.iloc[-1][metric])
        recent_med=float(recent[metric].median())
        recent_q25=float(recent[metric].quantile(.25))
        hist_min=float(x[metric].min())
        target=max(hist_min, min(recent_med,recent_q25 if recent_q25>0 else recent_med))
        qty=float(r.Cantidad_por_casa)
        rows.append({
            'Material_homologado':r.Material_homologado,'Variante_comparable':r.Variante_comparable,'Familia':r.Familia,
            'Sistema_costo':r.get('Sistema_costo',''),'Cantidad_por_casa':qty,'Precio_actual':current,'Precio_mediana_6m':recent_med,
            'Precio_meta':target,'Brecha_unitaria':max(current-target,0),'Ahorro_por_casa':max(current-target,0)*qty,
            'Proveedor_actual':x.iloc[-1].Proveedor,'Fecha_ultimo':latest_date,'Observaciones':len(x)
        })
    return pd.DataFrame(rows)

def supplier_scorecard(d, value_col):
    z=d[d.Valor_analisis.gt(0)].copy()
    g=z.groupby('Proveedor',as_index=False).agg(
        Gasto=('Valor_analisis','sum'),Compras=('Factura','nunique'),Materiales=('Variante_comparable','nunique'),
        Ultima_compra=('Fecha','max'),Fletes=('Es_flete','sum')
    )
    # Variabilidad de precio comparable por proveedor: mediana del CV por SKU.
    cvs=[]
    for (p,k),x in z[z.Precio_unitario.gt(0)].groupby(['Proveedor','Variante_comparable']):
        if len(x)>=2 and x.Precio_unitario.mean()>0:
            cvs.append((p,k,float(x.Precio_unitario.std(ddof=0)/x.Precio_unitario.mean())))
    cvdf=pd.DataFrame(cvs,columns=['Proveedor','Variante','CV']) if cvs else pd.DataFrame(columns=['Proveedor','Variante','CV'])
    medcv=cvdf.groupby('Proveedor',as_index=False).CV.median() if len(cvdf) else pd.DataFrame(columns=['Proveedor','CV'])
    g=g.merge(medcv,on='Proveedor',how='left')
    g['CV']=g.CV.fillna(g.CV.median() if g.CV.notna().any() else 0)
    # Score 0-100: recurrencia + amplitud de surtido + estabilidad de precios; no incluye calidad/OTIF por falta de datos.
    def norm(v, inverse=False):
        v=pd.Series(v,dtype=float)
        if v.max()==v.min(): out=pd.Series(np.ones(len(v))*0.5,index=v.index)
        else: out=(v-v.min())/(v.max()-v.min())
        return 1-out if inverse else out
    g['Score']=100*(.35*norm(g.Compras)+.25*norm(g.Materiales)+.40*norm(g.CV,inverse=True))
    return g.sort_values('Score',ascending=False)

def cost_drivers(d, recipe, price_col):
    # Drivers observables con los datos disponibles: cambio de precio por familia sobre una receta fija.
    t=recipe_cost_trend(d,recipe,price_col)
    valid=t[t.Comparable]
    if len(valid)<2: return pd.DataFrame()
    start_m,end_m=valid.iloc[0].Mes,valid.iloc[-1].Mes
    rr=recipe[~recipe.Confianza_receta.eq('Revisar sistema')][['Variante_comparable','Familia','Cantidad_por_casa']].copy()
    x=d[d.Fecha.notna() & d[price_col].gt(0)].copy()
    x['Mes']=x.Fecha.dt.to_period('M').dt.to_timestamp()
    obs=x.groupby(['Variante_comparable','Familia','Mes'],as_index=False)[price_col].median()
    rows=[]
    for _,r in rr.iterrows():
        q=float(r.Cantidad_por_casa)
        a=obs[(obs.Variante_comparable.eq(r.Variante_comparable)) & (obs.Mes<=start_m)].sort_values('Mes')
        b=obs[(obs.Variante_comparable.eq(r.Variante_comparable)) & (obs.Mes<=end_m)].sort_values('Mes')
        if a.empty or b.empty: continue
        p0=float(a.iloc[-1][price_col]); p1=float(b.iloc[-1][price_col])
        rows.append([r.Familia,q*(p1-p0)])
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows,columns=['Familia','Impacto']).groupby('Familia',as_index=False).Impacto.sum().sort_values('Impacto')



def structural_system_audit(d, value_col):
    cut=pd.Timestamp('2026-03-23')
    x=d.copy()
    desc=x.Descripcion_original.fillna('').str.lower()
    mat=x.Material_homologado.fillna('').str.lower()
    is_block=(mat.str.contains('block concreto',na=False) |
              desc.str.contains(r'\b(?:block|bloque)\b',regex=True,na=False))
    is_block &= ~desc.str.contains('zacate',na=False)
    is_block &= ~mat.str.contains('superblock',na=False)
    is_block &= ~desc.str.contains('superblock',na=False)
    block=x[is_block].copy()
    pre=block[block.Fecha.lt(cut)].copy()
    sb=x[x.Material_homologado.str.contains('Sistema Superblock',case=False,na=False) |
         x.Descripcion_original.str.contains('superblock',case=False,na=False)].copy()
    suppliers=(pre.groupby('Proveedor',as_index=False)
               .agg(Lineas=('Linea_id','count'),Cantidad=('Cantidad','sum'),Costo=(value_col,'sum'))
               .sort_values('Cantidad',ascending=False))
    evidence=pd.DataFrame([
        ['Block estructural previo al 23/03',float(pre.Cantidad.sum()),2550.0,float(pre.Cantidad.sum()/2550*100)],
        ['Block Casa 4 confirmado',2550.0,2550.0,100.0],
    ],columns=['Evidencia','Cantidad','Referencia_Casa4','Equivalencia_pct'])
    return {'pre_block':pre,'block_suppliers':suppliers,'superblock':sb,'evidence':evidence}


def house_1_2_overlap_audit(df, value_col):
    h=house_cost_history(df,value_col,100.0)
    c1=df[df.Fecha.between(pd.Timestamp('2024-11-01'),pd.Timestamp('2025-03-22'))].copy()
    c2=df[df.Fecha.between(pd.Timestamp('2025-03-23'),pd.Timestamp('2025-08-31'))].copy()
    finish_terms=['gypsum','pisos','enchapes','pintura','carpintería','mobiliario','adhesivos cerámicos',
                  'puertas','cerraduras','acabados','sanitarios','plomería','vidrios','cielos','selladores']
    def finish_mask(x):
        s=x.Familia.fillna('').str.lower()
        m=pd.Series(False,index=x.index)
        for term in finish_terms:
            m |= s.str.contains(term,regex=False)
        return m
    f1=float(c1.loc[finish_mask(c1),value_col].sum())
    f2=float(c2.loc[finish_mask(c2),value_col].sum())
    fam1=c1.groupby('Familia')[value_col].sum()
    fam2=c2.groupby('Familia')[value_col].sum()
    comp=pd.concat([fam1,fam2],axis=1,keys=['Casa1','Casa2']).fillna(0)
    comp['Delta']=comp.Casa2-comp.Casa1
    comp=comp.sort_values('Delta',ascending=False).reset_index()
    sb=df[df.Proveedor.str.contains('SUPERBLOQUE',case=False,na=False)].copy()
    sbqty=sb[(sb.Fecha==pd.Timestamp('2025-01-06')) & sb.Descripcion_original.str.contains('Sistema Mixto Superblock',case=False,na=False)]
    qty2=float(sbqty.Cantidad.sum()) if len(sbqty) else 0
    return {
        'c1':float(c1[value_col].sum()),'c2':float(c2[value_col].sum()),
        'delta':float(c2[value_col].sum()-c1[value_col].sum()),
        'pct':float((c2[value_col].sum()/c1[value_col].sum()-1)*100) if c1[value_col].sum() else np.nan,
        'finish1':f1,'finish2':f2,'finish_delta':f2-f1,
        'drivers':comp,'sb_qty_jan6':qty2
    }


def forensic_c1_c2_reconstruction(d, recipe, value_col, spill_days=90):
    """
    Reconstrucción conservadora Casa 1 vs Casa 2:
    1) detecta déficit de receta en Casa 1;
    2) busca exceso del mismo material en Casa 2;
    3) solo toma compras tempranas de la ventana 2 (spill_days) y componentes de etapa tardía;
    4) asigna costo usando las líneas/facturas reales;
    5) separa la factura Superbloque 25/03/2025 como 'estructural disputada',
       porque cae 2 días después del corte y coincide con acabados rezagados.
    """
    x=d.copy()
    c1_ini,c1_fin=pd.Timestamp('2024-11-01'),pd.Timestamp('2025-03-22')
    c2_ini,c2_fin=pd.Timestamp('2025-03-23'),pd.Timestamp('2025-08-31')
    c1=x[x.Fecha.between(c1_ini,c1_fin,inclusive='both')].copy()
    c2=x[x.Fecha.between(c2_ini,c2_fin,inclusive='both')].copy()

    # Expected quantity per homologated material from the standard recipe.
    exp=(recipe[~recipe.Confianza_receta.eq('Revisar sistema')]
         .groupby('Material_homologado',as_index=False)
         .Cantidad_por_casa.sum()
         .rename(columns={'Cantidad_por_casa':'Esperado'}))

    late_components={
        'Pisos / revestimientos','Divisiones / cielos','Instalación eléctrica',
        'Instalación hidrosanitaria','Pintura / acabados','Puertas / ventanas',
        'Baños / sanitarios','Carpintería / melamina'
    }
    q1=c1.groupby('Material_homologado').Cantidad.sum()
    q2=c2.groupby('Material_homologado').Cantidad.sum()
    cutoff=c2_ini+pd.Timedelta(days=spill_days)

    transfers=[]
    for _,er in exp.iterrows():
        mat=er.Material_homologado
        expected=float(er.Esperado or 0)
        if expected<=0:
            continue
        zmat=x[x.Material_homologado.eq(mat)]
        if zmat.empty:
            continue
        component=zmat.Componente_fisico.mode()
        component=component.iloc[0] if len(component) else 'Otros materiales de la vivienda'
        if component not in late_components:
            continue

        prev=float(q1.get(mat,0) or 0)
        nxt=float(q2.get(mat,0) or 0)
        deficit=max(expected-prev,0)
        surplus=max(nxt-expected,0)
        target=min(deficit,surplus)
        if target<=0:
            continue

        # Use actual early invoices from Casa-2 window; closest to boundary first.
        zz=c2[(c2.Material_homologado.eq(mat)) & (c2.Fecha<=cutoff)].sort_values(['Fecha','Factura','Linea_id'])
        remaining=target
        for _,r in zz.iterrows():
            if remaining<=1e-9:
                break
            qty=float(r.Cantidad or 0)
            if qty<=0:
                continue
            take=min(qty,remaining)
            unit_cost=float(r[value_col] or 0)/qty
            transfers.append({
                'Material':mat,'Componente':component,'Fecha':r.Fecha,'Factura':r.Factura,
                'Proveedor':r.Proveedor,'Cantidad_linea':qty,'Cantidad_reasignada':take,
                'Costo_reasignado':take*unit_cost,'Esperado_receta':expected,
                'Cantidad_Casa1_ventana':prev,'Cantidad_Casa2_ventana':nxt
            })
            remaining-=take

    tr=pd.DataFrame(transfers)
    moved=float(tr.Costo_reasignado.sum()) if len(tr) else 0.0

    # Structural invoice immediately after the cut: do not silently assign it.
    disputed=c2[
        c2.Proveedor.str.contains('SUPERBLOQUE',case=False,na=False) &
        c2.Fecha.eq(pd.Timestamp('2025-03-25'))
    ].copy()
    disputed_cost=float(disputed[value_col].sum()) if len(disputed) else 0.0
    disputed_system=float(disputed.loc[
        disputed.Descripcion_original.str.contains('Sistema Mixto Superblock',case=False,na=False),
        value_col
    ].sum()) if len(disputed) else 0.0

    raw1=float(c1[value_col].sum())
    raw2=float(c2[value_col].sum())
    # High-confidence material correction only.
    adj1=raw1+moved
    adj2=raw2-moved
    # Audit scenario: material spillover + structural invoice kept outside C2 until attribution is resolved.
    scenario2=adj2-disputed_cost

    detail=(tr.groupby(['Material','Componente'],as_index=False)
            .agg(Cantidad_reasignada=('Cantidad_reasignada','sum'),
                 Costo_reasignado=('Costo_reasignado','sum'),
                 Primera_factura=('Fecha','min'),
                 Ultima_factura=('Fecha','max'),
                 Esperado_receta=('Esperado_receta','max'),
                 Cantidad_Casa1_ventana=('Cantidad_Casa1_ventana','max'),
                 Cantidad_Casa2_ventana=('Cantidad_Casa2_ventana','max'))
            .sort_values('Costo_reasignado',ascending=False)) if len(tr) else pd.DataFrame()

    return {
        'raw1':raw1,'raw2':raw2,'moved':moved,'adj1':adj1,'adj2':adj2,
        'disputed_cost':disputed_cost,'disputed_system':disputed_system,
        'scenario2':scenario2,'transfers':tr,'detail':detail,'cutoff':cutoff,
        'disputed':disputed
    }


def reconstructed_house_costs(d, recipe, value_col, house_area):
    h=house_cost_history(d,value_col,house_area).copy()
    audit=forensic_c1_c2_reconstruction(d,recipe,value_col,spill_days=90)
    h['Costo_raw']=h.Costo
    h['Estado']='Ventana temporal'
    # Reconstruct C1 with identifiable late-stage material spillover.
    h.loc[h.Casa.eq('Casa 1'),'Costo']=audit['adj1']
    h.loc[h.Casa.eq('Casa 1'),'Estado']='Reconstruido · materiales rezagados'
    # For C2, present the audit scenario: remove the same spillover and hold disputed 25/03 structural invoice outside.
    h.loc[h.Casa.eq('Casa 2'),'Costo']=audit['scenario2']
    h.loc[h.Casa.eq('Casa 2'),'Estado']='Reconstruido · Superbloque 25/03 pendiente de atribución'
    h['Costo_m2']=h.Costo/house_area if house_area else np.nan
    h['Delta']=h.Costo.diff()
    h['Delta_pct']=h.Costo.pct_change()*100
    first=float(h.iloc[0].Costo) if len(h) else 0
    h['Indice']=h.Costo/first*100 if first else np.nan
    return h,audit

# ---------------- Sidebar / assumptions ----------------
df0=load_data()
with st.sidebar:
    st.header('⚙️ Supuestos')
    st.markdown("<div class='sourcebox'><b>Receta:</b> 4 casas esencialmente iguales. Materiales comunes = total consolidado ÷ 4; la estructura se analiza por sistema constructivo.</div>",unsafe_allow_html=True)
    st.markdown("<div class='sourcebox'><b>Excepción confirmada:</b> block, arena, cemento, piedra y varilla desde el 23/03/2026 corresponden a la Casa 4, construida sin sistema Superbloque.</div>",unsafe_allow_html=True)
    st.markdown("<div class='sourcebox'><b>🏗️ Sistema histórico:</b><br>Casa 1 = Superbloque<br>Casa 2 = Superbloque<br>Casa 3 = Superbloque<br>Casa 4 = block convencional.<br><small>Clasificación de trabajo basada en la evidencia de compras; evita atribuir todo el cambio de costo a eficiencia.</small></div>",unsafe_allow_html=True)
    st.markdown("<div class='sourcebox'><b>🎯 Principio del informe:</b><br>cada análisis debe terminar en una decisión: qué comprar, cuánto, cuándo, con quién, a qué precio objetivo y dónde está el ahorro.</div>",unsafe_allow_html=True)
    tax_pct=st.number_input('Impuesto para estimación (%)',min_value=0.0,max_value=30.0,value=13.0,step=0.5)
    price_view=st.radio('Vista monetaria',['Costo final con impuesto','Precio sin impuesto'],index=0)
    st.caption('La base recibida está sin impuesto. El monto con impuesto es una estimación según la tasa seleccionada.')
    house_area=st.number_input('Área estándar por casa (m²)',min_value=50.0,max_value=300.0,value=HOUSE_AREA_M2,step=1.0)
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
quality=recipe_quality(df,recipe)
abc=abc_recipe(recipe)
should=should_cost_table(df,recipe,price_view,value_col)
scorecard=supplier_scorecard(df,value_col)
drivers=cost_drivers(df,recipe,unit_price_col)
struct_audit=structural_system_audit(df,value_col)


st.markdown("<div class='hero'><div class='eyebrow'>Inteligencia de costos de construcción · V7 MASTER DECISION</div><h1>Construir Mejor</h1><p><b>La receta, el costo y la oportunidad detrás de cada casa.</b><br>Lo aprendido en cuatro viviendas se convierte en una receta auditable: primero validamos comparabilidad, después explicamos el costo y finalmente decidimos cómo comprar las próximas dos.</p></div>",unsafe_allow_html=True)

st.markdown("""
<div class='story-flow' style='grid-template-columns:repeat(5,minmax(0,1fr))'>
  <div class='story-step'><div class='n'>Historia</div><div class='big'>3 + 1</div><div class='small'>Casas 1–3 Superbloque · Casa 4 block convencional.</div></div>
  <div class='story-step'><div class='n'>Aprendizaje</div><div class='big'>1 receta</div><div class='small'>Qué necesita realmente una vivienda comparable.</div></div>
  <div class='story-step'><div class='n'>Diagnóstico</div><div class='big'>¿Por qué?</div><div class='small'>Precio, sistema, proveedor, mercado y calidad.</div></div>
  <div class='story-step'><div class='n'>Decisión</div><div class='big'>¿Qué hacemos?</div><div class='small'>Comprar, negociar, recotizar, esperar o validar.</div></div>
  <div class='story-step'><div class='n'>Resultado</div><div class='big'>Casas 5 + 6</div><div class='small'>Cantidad + proveedor + Should Cost + ahorro.</div></div>
</div>
""", unsafe_allow_html=True)

recipe_cost=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].Costo_por_casa.sum()
label_tax='impuesto estimado incluido' if price_view=='Costo final con impuesto' else 'sin impuesto'
st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Costo materiales / casa</div><div class='value'>{money(recipe_cost)}</div><div class='sub'>{label_tax}</div></div><div class='kpi'><div class='label'>Materiales / m²</div><div class='value'>{money(recipe_cost/house_area)}</div><div class='sub'>referencia · {house_area:.0f} m²</div></div><div class='kpi'><div class='label'>Base histórica</div><div class='value'>4 casas</div><div class='sub'>2.392 líneas auditadas</div></div><div class='kpi'><div class='label'>Costo confirmado</div><div class='value'>{quality['Pct_confirmado']:.1f}%</div><div class='sub'>resto = estimado total÷4</div></div></div>",unsafe_allow_html=True)

st.markdown("<div class='kpi-grid'><div class='kpi'><div class='label'>Sistema histórico</div><div class='value'>3 Superbloque</div><div class='sub'>Casas 1 · 2 · 3</div></div><div class='kpi'><div class='label'>Sistema convencional</div><div class='value'>1 casa</div><div class='sub'>Casa 4 · block convencional</div></div><div class='kpi'><div class='label'>Objetivo</div><div class='value'>Decidir</div><div class='sub'>no solo describir</div></div><div class='kpi'><div class='label'>Salida</div><div class='value'>Plan 5 + 6</div><div class='sub'>qué · cuánto · cuándo · con quién</div></div></div>",unsafe_allow_html=True)

tab_names=['🎬 Historia','🎯 Centro de decisiones','🛡️ Calidad','🏠 Receta','🧱 Sistemas','🏗️ Superbloque vs Block','📉 Tendencia de costos','🇨🇷 Mercado CR','💧 Drivers','🧩 Anatomía','🏪 Proveedores','🎯 Should Cost','📈 Precios']
if len(freight): tab_names.append('🚚 Fletes')
tab_names += ['🎯 Casas 5 y 6','🔎 Base maestra']
tabs=st.tabs(tab_names); T=dict(zip(tab_names,tabs))

# ---------------- HISTORIA / PORTADA EJECUTIVA ----------------

with T['🎬 Historia']:
    st.subheader('🧾 Costo de la receta estándar por casa')
    st.markdown("<div class='story-callout'><div class='headline'>Primero: ¿en qué se compone el costo de una casa?</div>Este gráfico NO representa una casa histórica específica. Representa la <b>receta estándar por vivienda</b> construida a partir de las 2.392 líneas auditadas: materiales comunes distribuidos entre cuatro casas y estructura tratada según las reglas confirmadas.</div>",unsafe_allow_html=True)

    rplot=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].copy()
    recipe_view=st.selectbox(
        'Visualización del costo de la receta',
        ['Treemap por familia','Pareto de costo','Sunburst familia → material','Donut por familia','Waterfall por familia'],
        key='cover_recipe_cost'
    )
    fam_recipe=(rplot.groupby('Familia',as_index=False)
                .agg(Costo=('Costo_por_casa','sum'),Materiales=('Material_homologado','nunique'))
                .sort_values('Costo',ascending=False))
    if recipe_view=='Treemap por familia':
        rfig=px.treemap(rplot,path=['Familia','Material_homologado'],values='Costo_por_casa',
                        hover_data=['Cantidad_por_casa','Confianza_receta'])
        rfig.update_layout(title='Composición del costo de la receta estándar',height=590)
        rread='Cada rectángulo es una familia o material. Mientras mayor sea el área, mayor es su peso en el costo estándar de una vivienda.'
    elif recipe_view=='Pareto de costo':
        q=fam_recipe.copy()
        q['Acum']=q.Costo.cumsum()/max(q.Costo.sum(),1)*100
        rfig=go.Figure()
        rfig.add_trace(go.Bar(x=q.Familia,y=q.Costo,name='Costo por familia'))
        rfig.add_trace(go.Scatter(x=q.Familia,y=q.Acum,yaxis='y2',mode='lines+markers',name='% acumulado'))
        rfig.update_layout(title='Pareto del costo de la receta',height=590,
                           yaxis_title='Costo por casa (₡)',
                           yaxis2=dict(overlaying='y',side='right',range=[0,105],title='% acumulado'))
        rread='Las barras ordenan las familias de mayor a menor costo. La línea muestra cuánto del presupuesto se acumula al sumar las familias principales.'
    elif recipe_view=='Sunburst familia → material':
        rfig=px.sunburst(rplot,path=['Familia','Material_homologado'],values='Costo_por_casa',
                         hover_data=['Cantidad_por_casa','Confianza_receta'])
        rfig.update_layout(title='Familia → material dentro de la receta',height=590)
        rread='El centro agrupa por familia y el segundo nivel abre los materiales. El tamaño de cada segmento representa su costo por casa.'
    elif recipe_view=='Donut por familia':
        rfig=px.pie(fam_recipe,values='Costo',names='Familia',hole=.55)
        rfig.update_layout(title='Distribución porcentual del costo estándar',height=590)
        rread='Cada segmento representa la participación de una familia en el costo de la receta. Los segmentos grandes son los principales focos de negociación.'
    else:
        q=fam_recipe.head(12).copy()
        rfig=go.Figure(go.Waterfall(
            x=q.Familia,measure=['relative']*len(q),y=q.Costo,
            text=[money(v) for v in q.Costo],textposition='outside'
        ))
        rfig.update_layout(title='Cómo se construye el costo de la receta · principales familias',height=590,yaxis_title='Costo por casa (₡)')
        rread='Cada barra agrega el costo de una familia a la receta estándar. Permite ver cuáles componentes construyen el costo total de una vivienda.'

    st.plotly_chart(rfig,use_container_width=True)
    topfam=fam_recipe.iloc[0] if len(fam_recipe) else None
    top3=fam_recipe.head(3).Costo.sum()/max(fam_recipe.Costo.sum(),1)*100 if len(fam_recipe) else 0
    explain(
        rread,
        f"Concentrar la negociación y el control de cantidades en las familias de mayor peso. {'La primera prioridad es '+str(topfam.Familia) if topfam is not None else 'Validar la receta antes de comprar'}.",
        f"Las tres familias de mayor costo concentran {top3:.1f}% de la receta estándar. El costo total estimado por casa es {money(rplot.Costo_por_casa.sum())}."
    )

    st.markdown('---')
    # Segundo gráfico de portada: costo histórico casa por casa.
    st.markdown('### 🏠 Costo reconstruido por casa · auditoría de solapes')
    cover_hc,cover_audit=reconstructed_house_costs(df,recipe,value_col,house_area)
    cover_view=st.selectbox(
        'Visualización de comparación casa por casa',
        ['Línea comparativa','Barras comparativas','Slope','Índice Casa 1 = 100','Costo por m²'],
        key='cover_house_compare'
    )
    if cover_view=='Línea comparativa':
        cover_fig=go.Figure(go.Scatter(
            x=cover_hc.Casa,y=cover_hc.Costo,mode='lines+markers+text',
            text=[f"{money(r.Costo)}<br>{r.Sistema}" for _,r in cover_hc.iterrows()],
            textposition='top center',
            customdata=np.c_[cover_hc.Sistema,cover_hc.Costo_m2,cover_hc.Delta_pct,cover_hc.Estado],
            hovertemplate='<b>%{x}</b><br>%{customdata[0]}<br>Costo: ₡%{y:,.0f}<br>₡/m²: ₡%{customdata[1]:,.0f}<br>Variación: %{customdata[2]:.1f}%<br>Estado: %{customdata[3]}<extra></extra>',
            line=dict(width=5),marker=dict(size=14)
        ))
        cover_fig.update_layout(title='Costo registrado por casa y sistema constructivo',yaxis_title='Costo registrado (₡)',height=570)
        cover_read='Cada punto representa una casa completa. La altura es su costo registrado y la etiqueta indica el sistema constructivo utilizado.'
    elif cover_view=='Barras comparativas':
        q=cover_hc.copy()
        q['Etiqueta']=[f"{money(r.Costo)}<br>{r.Sistema}<br>{'' if pd.isna(r.Delta_pct) else f'{r.Delta_pct:+.1f}% vs anterior'}" for _,r in q.iterrows()]
        cover_fig=px.bar(q,x='Casa',y='Costo',text='Etiqueta',hover_data=['Sistema','Costo_m2','Inicio','Fin'])
        cover_fig.update_traces(textposition='outside')
        cover_fig.update_layout(title='Costo total de construcción por casa',yaxis_title='Costo registrado (₡)',height=570)
        cover_read='La altura de cada barra permite comparar las cuatro viviendas. La etiqueta muestra costo, sistema y variación contra la casa anterior.'
    elif cover_view=='Slope':
        cover_fig=go.Figure()
        cover_fig.add_trace(go.Scatter(
            x=cover_hc.Casa,y=cover_hc.Costo,mode='lines+markers+text',
            text=[f"{r.Sistema}<br>{money(r.Costo)}" for _,r in cover_hc.iterrows()],
            textposition='top center',line=dict(width=5),marker=dict(size=14)
        ))
        cover_fig.update_layout(title='Pendiente del costo Casa 1 → Casa 4',yaxis_title='Costo registrado (₡)',height=570)
        cover_read='La pendiente muestra inmediatamente dónde subió o bajó el costo entre casas consecutivas; cada punto conserva el sistema usado.'
    elif cover_view=='Índice Casa 1 = 100':
        cover_fig=px.line(cover_hc,x='Casa',y='Indice',markers=True,text='Sistema')
        cover_fig.update_traces(textposition='top center',line=dict(width=5),marker=dict(size=14))
        cover_fig.add_hline(y=100,line_dash='dash',annotation_text='Casa 1 = 100')
        cover_fig.update_layout(title='Costo relativo · Casa 1 = 100',yaxis_title='Índice',height=570)
        cover_read='Casa 1 se convierte en la base 100. Un índice inferior a 100 significa que esa casa costó menos que Casa 1; uno superior significa que costó más.'
    else:
        cover_fig=px.line(cover_hc,x='Casa',y='Costo_m2',markers=True,text='Sistema')
        cover_fig.update_traces(textposition='top center',line=dict(width=5),marker=dict(size=14))
        cover_fig.update_layout(title=f'Costo por m² · referencia {house_area:.0f} m²',yaxis_title='₡/m²',height=570)
        cover_read=f'Cada punto divide el costo de la casa entre {house_area:.0f} m² de referencia. Sirve para comparar el costo unitario manteniendo visible el sistema.'
    st.plotly_chart(cover_fig,use_container_width=True)

    c1=cover_hc.iloc[0]; c4=cover_hc.iloc[-1]
    cover_change=(c4.Costo/c1.Costo-1)*100 if c1.Costo else np.nan
    cheapest=cover_hc.loc[cover_hc.Costo.idxmin()]
    most_expensive=cover_hc.loc[cover_hc.Costo.idxmax()]
    explain(
        cover_read,
        f"Usar esta comparación para identificar qué casa y sistema dejaron el mejor costo histórico y qué prácticas conviene trasladar a Casas 5 y 6. El primer foco de análisis debe ser la diferencia entre {most_expensive.Casa} y {cheapest.Casa}.",
        f"{most_expensive.Casa} registra el mayor costo ({money(most_expensive.Costo)}) y {cheapest.Casa} el menor ({money(cheapest.Costo)}). Casa 4, construida con block convencional, registra {money(c4.Costo)} y está {abs(cover_change):.1f}% {'por debajo' if cover_change<0 else 'por encima'} de Casa 1."
    )


    st.markdown('### 🕵️ Qué estaba cargado en Casa 2 y faltaba en Casa 1')
    ov=cover_audit
    st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Gasto raw Casa 1</div><div class='value'>{money(ov['raw1'])}</div><div class='sub'>antes de reconstrucción</div></div><div class='kpi'><div class='label'>Material rezagado identificado</div><div class='value'>{money(ov['moved'])}</div><div class='sub'>reasignado Casa 2 → Casa 1</div></div><div class='kpi'><div class='label'>Superbloque 25/03 en revisión</div><div class='value'>{money(ov['disputed_cost'])}</div><div class='sub'>2 días después del corte</div></div><div class='kpi'><div class='label'>Casa 2 · escenario auditado</div><div class='value'>{money(ov['scenario2'])}</div><div class='sub'>sin solape + factura estructural disputada</div></div></div>",unsafe_allow_html=True)

    if len(ov['detail']):
        matv=ov['detail'].head(18).sort_values('Costo_reasignado')
        mfig=px.bar(matv,x='Costo_reasignado',y='Material',orientation='h',
                    hover_data=['Componente','Cantidad_reasignada','Esperado_receta',
                                'Cantidad_Casa1_ventana','Cantidad_Casa2_ventana',
                                'Primera_factura','Ultima_factura'])
        mfig.update_layout(title='Materiales detectados en exceso en la ventana Casa 2 y deficitarios en Casa 1',
                           xaxis_title='Costo reasignado a Casa 1 (₡)',height=650)
        st.plotly_chart(mfig,use_container_width=True)
        explain(
            'Para cada material se compara la cantidad esperada de la receta con lo comprado en ambas ventanas. Solo se reasignan compras de etapas tardías hechas durante los primeros 90 días después del corte y únicamente cuando Casa 1 tiene déficit y Casa 2 tiene exceso.',
            'Usar la reconstrucción como costo histórico de trabajo y mantener las líneas de baja certeza abiertas hasta validar con la secuencia de obra o evidencia adicional.',
            f"Se identificaron {len(ov['detail'])} materiales con patrón compatible con solape, por {money(ov['moved'])}. Los de mayor impacto son " + ', '.join(ov['detail'].head(5).Material.astype(str).tolist()) + "."
        )
        st.dataframe(
            ov['detail'][['Material','Componente','Cantidad_Casa1_ventana','Esperado_receta',
                          'Cantidad_Casa2_ventana','Cantidad_reasignada','Costo_reasignado',
                          'Primera_factura','Ultima_factura']].head(30),
            use_container_width=True,hide_index=True
        )

    st.markdown('### 🧱 La diferencia restante: factura Superbloque del 25/03/2025')
    st.warning(f"Después de devolver a Casa 1 los materiales tardíos identificables, todavía queda una diferencia importante. El principal elemento es la factura Superbloque del 25/03/2025 por {money(ov['disputed_cost'])}, de los cuales {money(ov['disputed_system'])} corresponden al Sistema Mixto Superblock. Está apenas 2 días después del corte y coincide con compras de acabados de la vivienda anterior. Por eso el gráfico reconstruido NO la carga automáticamente a Casa 2: la mantiene como costo estructural pendiente de atribución.")
    if len(ov['disputed']):
        st.dataframe(
            ov['disputed'][['Fecha','Factura','Proveedor','Descripcion_original','Cantidad','Total_linea']].copy(),
            use_container_width=True,hide_index=True
        )
    st.markdown(f"<div class='sourcebox'><b>Resultado de la reconstrucción Casa 1–Casa 2:</b> Casa 1 pasa de {money(ov['raw1'])} a aproximadamente <b>{money(ov['adj1'])}</b> al recibir materiales tardíos que su receta necesitaba. Casa 2 pasa de {money(ov['raw2'])} a <b>{money(ov['adj2'])}</b> por esa misma corrección. Si además se mantiene fuera de Casa 2 la factura estructural disputada del 25/03 hasta resolver a qué vivienda corresponde, el escenario auditado de Casa 2 queda en aproximadamente <b>{money(ov['scenario2'])}</b>. Esto explica por qué la diferencia inicial parecía artificialmente grande.</div>",unsafe_allow_html=True)

    st.markdown('### 🏠 Costo y sistema, casa por casa')
    cols=st.columns(4)
    for i,(_,r) in enumerate(cover_hc.iterrows()):
        var='Punto de partida' if pd.isna(r.Delta_pct) else f"{r.Delta_pct:+.1f}% vs anterior"
        cols[i].markdown(f"<div class='card'><div class='title'>{r.Casa}</div><div class='big'>{money(r.Costo)}</div><div class='meta'><b>{r.Sistema}</b><br>{money(r.Costo_m2)}/m²<br>{var}<br>{r.Inicio:%d/%m/%Y} → {r.Fin:%d/%m/%Y}</div></div>",unsafe_allow_html=True)

    st.markdown('### 🔎 ¿Por qué cambió el costo?')
    st.markdown("<div class='sourcebox'>La gráfica anterior responde <b>cuánto costó cada casa</b>. Las secciones de Sistemas, Drivers, Proveedores, Should Cost y Precios responden <b>por qué cambió</b>. Así evitamos confundir la tendencia principal con una serie mensual de compras.</div>",unsafe_allow_html=True)

    # Secondary story/decision visuals retained, but no longer replace the house-cost trend.
    story_recipe=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].copy()
    story_cost=story_recipe.Costo_por_casa.sum()
    story_plan=plan_future(df,recipe,value_col,price_view,2,waste)
    story_saving=story_plan.Ahorro_potencial.sum() if len(story_plan) else np.nan
    st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Receta estándar</div><div class='value'>{money(story_cost)}</div><div class='sub'>referencia por casa</div></div><div class='kpi'><div class='label'>Mejor costo histórico</div><div class='value'>{money(cheapest.Costo)}</div><div class='sub'>{cheapest.Casa} · {cheapest.Sistema}</div></div><div class='kpi'><div class='label'>Cambio Casa 1 → 4</div><div class='value'>{cover_change:+.1f}%</div><div class='sub'>{money(c4.Costo-c1.Costo)}</div></div><div class='kpi'><div class='label'>Oportunidad Casas 5+6</div><div class='value'>{money(story_saving)}</div><div class='sub'>vs precio meta de compra</div></div></div>",unsafe_allow_html=True)



# ---------------- CENTRO DE DECISIONES ----------------
with T['🎯 Centro de decisiones']:
    st.subheader('🎯 Centro de decisiones · de insight a acción')
    st.markdown("<div class='story-callout'><div class='headline'>Esta es la salida ejecutiva del informe.</div>No resume gráficos: prioriza acciones para Casas 5 y 6 según impacto económico, tendencia, brecha contra Should Cost y confiabilidad de la receta.</div>",unsafe_allow_html=True)
    dc_plan=plan_future(df,recipe,value_col,price_view,2,waste)
    dc_should=should.sort_values('Ahorro_por_casa',ascending=False).copy() if len(should) else should
    dc_abc=abc.copy()
    a_count=int((dc_abc.ABC=='A').sum()) if len(dc_abc) else 0
    op2=float(dc_should.Ahorro_por_casa.sum()*2) if len(dc_should) else 0
    topmat=dc_should.iloc[0].Material_homologado if len(dc_should) else '—'
    rising=int((dc_plan.Tendencia=='Subiendo').sum()) if len(dc_plan) else 0
    st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Oportunidad estimada 2 casas</div><div class='value'>{money(op2)}</div><div class='sub'>brecha vs Should Cost</div></div><div class='kpi'><div class='label'>Materiales clase A</div><div class='value'>{a_count}</div><div class='sub'>núcleo del presupuesto</div></div><div class='kpi'><div class='label'>Materiales al alza</div><div class='value'>{rising}</div><div class='sub'>revisar timing de compra</div></div><div class='kpi'><div class='label'>Mayor oportunidad</div><div class='value'>{topmat}</div><div class='sub'>primera negociación</div></div></div>",unsafe_allow_html=True)

    if len(dc_plan):
        act=dc_plan.copy()
        act['Impacto']=act.Ahorro_potencial.fillna(0)
        act['Accion']=np.select(
            [
                act.Confianza_receta.eq('Estimado'),
                act.Tendencia.eq('Subiendo') & act.Ahorro_potencial.gt(0),
                act.Ahorro_potencial.gt(0),
                act.Tendencia.eq('Bajando')
            ],
            ['VALIDAR CANTIDAD','COTIZAR / NEGOCIAR AHORA','NEGOCIAR','RECOTIZAR / ESPERAR'],
            default='MANTENER / MONITOREAR'
        )
        act['Prioridad_score']=np.log1p(act.Costo_estimado.clip(lower=0))*(1+np.log1p(act.Ahorro_potencial.clip(lower=0)))
        act=act.sort_values(['Impacto','Prioridad_score'],ascending=False)
        dv=st.selectbox('Visualización del centro de decisiones',[
            'Ranking de acciones','Matriz impacto × tendencia','Pareto de ahorro',
            'Treemap acción → material','Sankey acción → proveedor','Heatmap acción × familia'
        ])
        top=act.head(30)
        if dv=='Ranking de acciones':
            fig=px.bar(top.sort_values('Impacto'),x='Impacto',y='Material_homologado',orientation='h',color='Accion',hover_data=['Proveedor_1','Precio_actual','Precio_meta','Tendencia'])
            read='Cada barra es el ahorro potencial de un material; el color indica la acción recomendada. Arriba quedan las oportunidades de mayor impacto.'
        elif dv.startswith('Matriz'):
            trend_num=top.Tendencia.map({'Bajando':-1,'Estable':0,'Subiendo':1}).fillna(0)
            fig=px.scatter(top,x='Costo_estimado',y=trend_num,size=np.maximum(top.Impacto,1),color='Accion',hover_name='Material_homologado',hover_data=['Proveedor_1','Precio_meta'])
            fig.update_yaxes(tickvals=[-1,0,1],ticktext=['Bajando','Estable','Subiendo'],title='Tendencia')
            read='A la derecha están los materiales de mayor presupuesto; arriba los que suben de precio; el tamaño representa la oportunidad económica.'
        elif dv.startswith('Pareto'):
            p=top.sort_values('Impacto',ascending=False).copy(); p['Acum']=p.Impacto.cumsum()/max(p.Impacto.sum(),1)*100
            fig=go.Figure([go.Bar(x=p.Material_homologado,y=p.Impacto,name='Ahorro'),go.Scatter(x=p.Material_homologado,y=p.Acum,yaxis='y2',mode='lines+markers',name='% acumulado')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
            read='Las barras ordenan oportunidades de mayor a menor; la línea indica cuánto del ahorro total se acumula al negociar los primeros materiales.'
        elif dv.startswith('Treemap'):
            fig=px.treemap(top,path=['Accion','Material_homologado'],values=np.maximum(top.Impacto,1),hover_data=['Proveedor_1','Precio_meta'])
            read='El área de cada bloque representa el impacto; primero se agrupa por acción y luego por material.'
        elif dv.startswith('Sankey'):
            z=top.head(20); actions=list(dict.fromkeys(z.Accion)); provs=list(dict.fromkeys(z.Proveedor_1)); labels=actions+provs; src=[];tgt=[];val=[]
            for _,r in z.iterrows():
                src.append(labels.index(r.Accion)); tgt.append(labels.index(r.Proveedor_1)); val.append(max(float(r.Costo_estimado),1))
            fig=go.Figure(go.Sankey(node=dict(label=labels,pad=12,thickness=16),link=dict(source=src,target=tgt,value=val)))
            read='Los flujos conectan la acción recomendada con el proveedor sugerido; el grosor representa el presupuesto involucrado.'
        else:
            h=top.pivot_table(index='Familia',columns='Accion',values='Impacto',aggfunc='sum',fill_value=0)
            fig=px.imshow(h,aspect='auto',text_auto='.2s')
            read='Las celdas cruzan familia y acción; los valores altos señalan dónde concentrar negociación o validación.'
        fig.update_layout(height=610,title='¿Dónde debemos actuar primero?')
        st.plotly_chart(fig,use_container_width=True)
        best=act.iloc[0]
        explain(
            read,
            f"Priorizar {best.Material_homologado}: {best.Accion.lower()}, cotizar primero con {best.Proveedor_1} y usar {money(best.Precio_meta)} como referencia de negociación.",
            f"La mayor oportunidad visible es {best.Material_homologado}, con {money(best.Ahorro_potencial)} de ahorro potencial en el plan seleccionado y tendencia {best.Tendencia.lower()}."
        )

        st.markdown('### 🧭 Lista ejecutiva de acciones')
        show=act[['Accion','Material_homologado','Familia','Cantidad_meta','Proveedor_1','Proveedor_2','Precio_actual','Precio_meta','Tendencia','Ahorro_potencial','Confianza_receta']].head(20)
        st.dataframe(show,use_container_width=True,hide_index=True)
        st.markdown("<div class='sourcebox'><b>Regla de uso:</b> 🔴 cotizar/negociar ahora = alto impacto y/o precio al alza · 🟠 negociar = existe brecha contra meta · 🔵 recotizar/esperar = tendencia bajando · ⚠️ validar cantidad = receta estimada antes de comprometer compra.</div>",unsafe_allow_html=True)
    else:
        st.warning('No hay suficiente información comparable para construir acciones automáticas.')


# ---------------- CALIDAD / VALIDACIÓN ----------------
with T['🛡️ Calidad']:
    st.subheader('🛡️ Confianza antes del gráfico')
    st.markdown("<div class='story-callout'><div class='headline'>Primero validamos la base; después interpretamos los gráficos.</div>La V7 separa datos confirmados, estimados y elementos que requieren tratamiento especial para evitar una falsa precisión.</div>",unsafe_allow_html=True)
    a,b,c,dq=st.columns(4)
    a.metric('Líneas auditadas',f"{len(df):,}")
    b.metric('Costo confirmado',f"{quality['Pct_confirmado']:.1f}%")
    c.metric('Costo estimado ÷4',f"{quality['Pct_estimado']:.1f}%")
    dq.metric('Sistemas por revisar',quality['Grupos_revisar'])
    st.markdown("### Correcciones de calidad aplicadas antes del cálculo")
    qrules=df[df.Regla_calidad_v7.ne('')].groupby('Regla_calidad_v7',as_index=False).agg(Lineas=('Linea_id','count'),Impacto_historico=('Valor_analisis','sum'))
    st.dataframe(qrules,use_container_width=True,hide_index=True)
    st.caption('Estas líneas permanecen en la base histórica para auditoría, pero su clasificación analítica evita que contaminen la receta o la tendencia.')
    st.markdown("### Controles estructurales confirmados")
    structural=pd.DataFrame([
        ['Cemento gris 50 kg',272,'sacos'],['Arena',39,'m³'],['Piedra / agregado',27,'m³'],
        ['Block 12×20×40',1710,'unidades'],['Block 15×20×40',840,'unidades'],
        ['Varilla #3 × 6 m',651,'unidades'],['Varilla #4 × 6 m',60,'unidades']
    ],columns=['Material','Cantidad por casa','Unidad'])
    st.dataframe(structural,use_container_width=True,hide_index=True)
    st.markdown("### Cobertura metodológica de la receta")
    qv=st.selectbox('Visualización de calidad',['Barras de cobertura','Treemap por confianza','Sunburst confianza → familia','Pareto de grupos estimados','Heatmap confianza × sistema'])
    rq=recipe.copy()
    if qv.startswith('Barras'):
        z=rq.groupby('Confianza_receta',as_index=False).Costo_por_casa.sum(); fig=px.bar(z,x='Confianza_receta',y='Costo_por_casa',text_auto='.2s')
    elif qv.startswith('Treemap'): fig=px.treemap(rq,path=['Confianza_receta','Familia'],values='Costo_por_casa')
    elif qv.startswith('Sunburst'): fig=px.sunburst(rq,path=['Confianza_receta','Familia'],values='Costo_por_casa')
    elif qv.startswith('Pareto'):
        z=rq[rq.Confianza_receta.eq('Estimado')].sort_values('Costo_por_casa',ascending=False).head(30); z['Acum']=z.Costo_por_casa.cumsum()/max(z.Costo_por_casa.sum(),1)*100
        fig=go.Figure([go.Bar(x=z.Material_homologado,y=z.Costo_por_casa),go.Scatter(x=z.Material_homologado,y=z.Acum,yaxis='y2',mode='lines+markers')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
    else:
        z=rq.pivot_table(index='Sistema_costo',columns='Confianza_receta',values='Costo_por_casa',aggfunc='sum',fill_value=0); fig=px.imshow(z,aspect='auto',text_auto='.2s')
    fig.update_layout(height=520)
    st.plotly_chart(fig,use_container_width=True)
    explain('Muestra qué parte de la receta proviene de evidencia directa y qué parte se estima dividiendo el consolidado entre cuatro.','Priorizar futuras validaciones en los grupos estimados de mayor impacto económico.')

# ---------------- SISTEMAS / CBS ----------------
with T['🧱 Sistemas']:
    st.subheader('🧱 Cost Breakdown Structure · costo por sistema')
    sys=recipe[~recipe.Confianza_receta.eq('Revisar sistema')].groupby('Sistema_costo',as_index=False).agg(Costo_por_casa=('Costo_por_casa','sum'),Grupos=('Variante_comparable','nunique'))
    sys['Costo_por_m2']=sys.Costo_por_casa/house_area
    sys['Participacion_pct']=sys.Costo_por_casa/max(sys.Costo_por_casa.sum(),1)*100
    a,b,c=st.columns(3)
    top=sys.sort_values('Costo_por_casa',ascending=False).iloc[0]
    a.metric('Sistema de mayor costo',top.Sistema_costo)
    b.metric('Costo del sistema',money(top.Costo_por_casa))
    c.metric('Materiales / m²',money(recipe_cost/house_area))
    sv=st.selectbox('Visualización por sistema',['Treemap de sistemas','Sunburst sistema → familia','Barras costo / m²','Pareto de sistemas','Waterfall de composición'])
    if sv.startswith('Treemap'): fig=px.treemap(sys,path=['Sistema_costo'],values='Costo_por_casa',hover_data=['Costo_por_m2','Participacion_pct'])
    elif sv.startswith('Sunburst'):
        z=recipe[~recipe.Confianza_receta.eq('Revisar sistema')]; fig=px.sunburst(z,path=['Sistema_costo','Familia'],values='Costo_por_casa')
    elif sv.startswith('Barras'): fig=px.bar(sys.sort_values('Costo_por_m2'),x='Costo_por_m2',y='Sistema_costo',orientation='h',text_auto='.2s')
    elif sv.startswith('Pareto'):
        z=sys.sort_values('Costo_por_casa',ascending=False); z['Acum']=z.Costo_por_casa.cumsum()/max(z.Costo_por_casa.sum(),1)*100
        fig=go.Figure([go.Bar(x=z.Sistema_costo,y=z.Costo_por_casa),go.Scatter(x=z.Sistema_costo,y=z.Acum,yaxis='y2',mode='lines+markers')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
    else:
        z=sys.sort_values('Costo_por_casa',ascending=False); fig=go.Figure(go.Waterfall(x=z.Sistema_costo,y=z.Costo_por_casa,measure=['relative']*len(z)))
    fig.update_layout(height=560,title='¿Qué parte de la casa consume el presupuesto de materiales?')
    st.plotly_chart(fig,use_container_width=True)
    explain('Agrupa la receta por sistemas de la vivienda, no solo por nombre de producto. El indicador ₡/m² es exclusivamente de materiales.','Enfocar ingeniería de valor y negociación en los sistemas que dominan el costo.')

# ---------------- MERCADO COSTA RICA ----------------
with T['🇨🇷 Mercado CR']:
    st.subheader('🇨🇷 Construir Mejor vs mercado costarricense')
    st.caption('Benchmark: Índice de Precios de Edificios del INEC, base febrero 2025. Serie oficial incorporada hasta julio 2026.')
    rt=trend[trend.Comparable][['Mes','Indice','Costo_receta']].copy()
    market=INEC_BUILDINGS_2026.copy()
    if len(rt):
        rt26=rt[rt.Mes.between(pd.Timestamp('2026-01-01'),pd.Timestamp('2026-07-01'))].copy()
        if len(rt26):
            rt26['Construir_Mejor']=rt26.Costo_receta/rt26.iloc[0].Costo_receta*100
            market=market.merge(rt26[['Mes','Construir_Mejor']],on='Mes',how='left')
    market['INEC_base_periodo']=market.INEC_Edificios/market.iloc[0].INEC_Edificios*100
    mv=st.selectbox('Visualización benchmark',['Líneas base 100','Área comparativa','Diferencial vs mercado','Slope inicio → último','Tabla índice y brecha'])
    if mv=='Líneas base 100':
        z=market.melt('Mes',value_vars=['INEC_base_periodo','Construir_Mejor'],var_name='Serie',value_name='Indice'); fig=px.line(z,x='Mes',y='Indice',color='Serie',markers=True)
    elif mv=='Área comparativa':
        z=market.melt('Mes',value_vars=['INEC_base_periodo','Construir_Mejor'],var_name='Serie',value_name='Indice'); fig=px.area(z,x='Mes',y='Indice',color='Serie')
    elif mv=='Diferencial vs mercado':
        z=market.dropna(subset=['Construir_Mejor']).copy(); z['Brecha']=z.Construir_Mejor-z.INEC_base_periodo; fig=px.bar(z,x='Mes',y='Brecha',text_auto='.1f')
    elif mv.startswith('Slope'):
        z=market.dropna(subset=['Construir_Mejor'])
        fig=go.Figure()
        if len(z)>=2:
            for col,name in [('INEC_base_periodo','Mercado INEC'),('Construir_Mejor','Construir Mejor')]:
                fig.add_trace(go.Scatter(x=[z.iloc[0].Mes,z.iloc[-1].Mes],y=[z.iloc[0][col],z.iloc[-1][col]],mode='lines+markers+text',text=[f"{z.iloc[0][col]:.1f}",f"{z.iloc[-1][col]:.1f}"],name=name))
    else:
        fig=go.Figure(go.Table(header=dict(values=['Mes','INEC Edificios','INEC base Ene-26','Construir Mejor']),cells=dict(values=[market.Mes.dt.strftime('%Y-%m'),market.INEC_Edificios.round(3),market.INEC_base_periodo.round(2),market.Construir_Mejor.round(2)])))
    fig.update_layout(height=520,title='¿Mejoramos nosotros o se movió el mercado?')
    st.plotly_chart(fig,use_container_width=True)
    explain('Ambas series se llevan a base 100 en el mismo período visible. INEC representa el mercado; Construir Mejor representa el costo de nuestra receta fija.','Separar el efecto mercado de la eficiencia propia de compra. No interpreta correlación como causalidad.')

# ---------------- DRIVERS ----------------
with T['💧 Drivers']:
    st.subheader('💧 ¿Qué está moviendo el costo?')
    if drivers.empty:
        st.warning('Cobertura histórica insuficiente para descomponer drivers.')
    else:
        dv=st.selectbox('Visualización de drivers',['Waterfall por familia','Pareto de impacto','Barras positivas/negativas','Treemap impacto absoluto','Heatmap familia × signo'])
        z=drivers.copy(); z['Impacto_abs']=z.Impacto.abs(); z['Signo']=np.where(z.Impacto<=0,'Ahorro / reducción','Incremento')
        if dv.startswith('Waterfall'): fig=go.Figure(go.Waterfall(x=z.Familia,y=z.Impacto,measure=['relative']*len(z)))
        elif dv.startswith('Pareto'):
            p=z.sort_values('Impacto_abs',ascending=False); p['Acum']=p.Impacto_abs.cumsum()/max(p.Impacto_abs.sum(),1)*100; fig=go.Figure([go.Bar(x=p.Familia,y=p.Impacto_abs),go.Scatter(x=p.Familia,y=p.Acum,yaxis='y2',mode='lines+markers')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
        elif dv.startswith('Barras'): fig=px.bar(z.sort_values('Impacto'),x='Impacto',y='Familia',orientation='h',text_auto='.2s')
        elif dv.startswith('Treemap'): fig=px.treemap(z,path=['Signo','Familia'],values='Impacto_abs')
        else:
            h=z.pivot_table(index='Familia',columns='Signo',values='Impacto_abs',aggfunc='sum',fill_value=0); fig=px.imshow(h,aspect='auto',text_auto='.2s')
        fig.update_layout(height=560,title='Contribución observable del cambio de precio sobre una receta fija')
        st.plotly_chart(fig,use_container_width=True)
        explain('Mantiene las cantidades de la receta constantes y atribuye el cambio monetario a la variación de precios por familia.','Identificar dónde se generó ahorro y dónde la inflación/precio está erosionando la mejora.')

# ---------------- SHOULD COST ----------------
with T['🎯 Should Cost']:
    st.subheader('🎯 Should Cost · cuánto deberíamos pagar')
    st.caption('Precio meta estadístico: combina mínimo histórico con el cuartil inferior/mediana de los últimos 180 días. No sustituye una cotización vigente.')
    if should.empty:
        st.warning('No hay suficiente historial comparable.')
    else:
        total_op=should.Ahorro_por_casa.sum()
        a,b,c=st.columns(3)
        a.metric('Oportunidad / casa',money(total_op))
        b.metric('SKUs con brecha',int(should.Brecha_unitaria.gt(0).sum()))
        c.metric('Mayor oportunidad',should.sort_values('Ahorro_por_casa',ascending=False).iloc[0].Material_homologado)
        shv=st.selectbox('Visualización Should Cost',['Ranking de oportunidad','Waterfall de ahorro','Actual vs meta','Pareto de oportunidad','Heatmap sistema × oportunidad'])
        z=should.sort_values('Ahorro_por_casa',ascending=False).head(30)
        if shv.startswith('Ranking'): fig=px.bar(z.sort_values('Ahorro_por_casa'),x='Ahorro_por_casa',y='Material_homologado',orientation='h',text_auto='.2s')
        elif shv.startswith('Waterfall'): fig=go.Figure(go.Waterfall(x=z.Material_homologado,y=-z.Ahorro_por_casa,measure=['relative']*len(z)))
        elif shv.startswith('Actual'):
            fig=go.Figure(); fig.add_trace(go.Bar(y=z.Material_homologado,x=z.Precio_actual,name='Actual',orientation='h')); fig.add_trace(go.Bar(y=z.Material_homologado,x=z.Precio_meta,name='Meta',orientation='h')); fig.update_layout(barmode='group')
        elif shv.startswith('Pareto'):
            p=z.copy(); p['Acum']=p.Ahorro_por_casa.cumsum()/max(p.Ahorro_por_casa.sum(),1)*100; fig=go.Figure([go.Bar(x=p.Material_homologado,y=p.Ahorro_por_casa),go.Scatter(x=p.Material_homologado,y=p.Acum,yaxis='y2',mode='lines+markers')]); fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
        else:
            h=should.pivot_table(index='Familia',values='Ahorro_por_casa',aggfunc='sum'); fig=px.imshow(h,aspect='auto',text_auto='.2s')
        fig.update_layout(height=600,title='Brecha entre último precio observado y precio meta')
        st.plotly_chart(fig,use_container_width=True)
        explain('La brecha se multiplica por la cantidad estándar de una casa para convertir una diferencia de precio en impacto económico.','Preparar negociación y priorizar cotizaciones de alto impacto.')


# ---------------- RECETA ----------------
with T['🏠 Receta']:
    st.subheader('🏠 Receta estándar de una vivienda')
    st.metric('Costo de materiales / m²',money(recipe_cost/house_area),help='No incluye mano de obra, permisos, profesionales ni indirectos no presentes en la base.')
    st.markdown("<div class='sourcebox'><b>Metodología:</b> materiales comunes = total histórico ÷ 4. La estructura de Casa 4 usa cantidades reales desde 23/03/2026. Superbloque y block convencional previo permanecen separados para no crear una receta estructural ficticia.</div>",unsafe_allow_html=True)
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


# ---------------- SUPERBLOQUE VS BLOCK ----------------
with T['🏗️ Superbloque vs Block']:
    st.subheader('🏗️ Superbloque vs Block · reconciliación estructural')
    st.info('Casa 4 está confirmada como construcción sin Superbloque. Las Casas 1–3 no se fuerzan a una clasificación individual hasta que la evidencia física permita demostrarla.')
    pre_total=float(struct_audit['pre_block'].Cantidad.sum())
    a,b,c=st.columns(3)
    a.metric('Block estructural antes 23/03',f'{pre_total:,.0f} u')
    b.metric('Equivalente vs Casa 4',f'{pre_total/2550*100:.1f}%')
    c.metric('Block confirmado Casa 4','2.550 u')
    st.markdown('### Origen del block previo al 23/03')
    st.dataframe(struct_audit['block_suppliers'],use_container_width=True,hide_index=True)
    st.caption('Validado en la base: El Lagar = 460 unidades; EPA = 400 unidades. Zacate Block queda excluido.')
    sv=st.selectbox('Visualización comparación estructural',
        ['Block previo vs Casa 4','Block por proveedor','Evidencia porcentual','Compras Superbloque en el tiempo','Detalle de block previo'])
    if sv=='Block previo vs Casa 4':
        z=pd.DataFrame({'Escenario':['Previo 23/03','Casa 4 convencional'],'Cantidad':[pre_total,2550]})
        fig=px.bar(z,x='Escenario',y='Cantidad',text_auto='.0f')
    elif sv=='Block por proveedor':
        z=struct_audit['block_suppliers'].sort_values('Cantidad')
        fig=px.bar(z,x='Cantidad',y='Proveedor',orientation='h',text_auto='.0f')
    elif sv=='Evidencia porcentual':
        z=struct_audit['evidence']
        fig=px.bar(z,x='Equivalencia_pct',y='Evidencia',orientation='h',text_auto='.1f'); fig.add_vline(x=100,line_dash='dot')
    elif sv=='Compras Superbloque en el tiempo':
        z=struct_audit['superblock'].groupby('Fecha',as_index=False)[value_col].sum()
        fig=px.bar(z,x='Fecha',y=value_col,text_auto='.2s')
    else:
        z=struct_audit['pre_block'].sort_values('Fecha')
        fig=px.bar(z,x='Fecha',y='Cantidad',hover_data=['Proveedor','Descripcion_original','Factura'],text_auto='.0f')
    fig.update_layout(height=520,title='Reconciliación física del sistema estructural')
    st.plotly_chart(fig,use_container_width=True)
    st.warning('Los 860 blocks previos equivalen a 33,7% de la huella de 2.550 blocks de Casa 4. Prueban uso de block convencional antes de Casa 4, pero no bastan por sí solos para declarar otra vivienda completa de block.')
    st.markdown('**Regla final:** materiales comunes ÷4; estructura Casa 4 = cantidades reales desde 23/03; Superbloque separado; block previo conservado como evidencia sin repartirlo artificialmente entre Casas 1–3.')


# ---------------- TENDENCIA ----------------
with T['📉 Tendencia de costos']:
    st.subheader('📉 ¿Está bajando el costo de construir la misma casa?')
    rt=trend[trend.Comparable].copy()
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
    st.markdown("<div class='sourcebox'><b>Referencia física por casa:</b> 2 habitaciones · 2 baños completos en planta alta (uno por habitación) · 1 medio baño en planta baja · 3 inodoros · 3 lavamanos · 2 duchas · 3 muebles de melamina de referencia · 3 ventanas superiores + 1 ventana en planta baja · 1 puerta principal · puertas interiores según evidencia · 1 puerta de patio de 3 paneles · 1 cubierta frontal de policarbonato.</div>",unsafe_allow_html=True)
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
        ['Habitaciones',2,'Referencia de diseño'],['Baños completos',2,'Uno por habitación en planta alta'],['Medio baño',1,'Planta baja'],['Inodoros',3,'2 completos + 1 medio baño'],['Lavamanos',3,'2 completos + 1 medio baño'],['Duchas',2,'Baños completos'],['Muebles de melamina',3,'2 dormitorios + cocina'],['Ventanas superiores',3,'2 dormitorios + baño'],['Ventana planta baja',1,'Referencia de diseño'],['Puerta principal',1,'Referencia de diseño'],['Puerta servicio/medio baño',1,'Referencia de diseño'],['Puerta patio 3 paneles',1,'Referencia de diseño'],['Cubierta frontal policarbonato',1,'Referencia de diseño']
    ],columns=['Elemento','Cantidad esperada por casa','Validación'])
    st.dataframe(targets,use_container_width=True,hide_index=True)
    if len(services):
        st.caption('Servicios (por ejemplo cortes) se mantienen fuera de la cantidad física de materiales y se analizan como costo complementario, para no contaminar la receta material.')

# ---------------- PROVEEDORES ----------------
with T['🏪 Proveedores']:
    st.subheader('🏪 Supplier Scorecard')
    st.caption('Score disponible con los datos actuales: recurrencia, amplitud de materiales y estabilidad de precios. Calidad, OTIF y lead time quedan fuera hasta contar con esos datos.')
    top_sc=scorecard.head(15)
    scv=st.selectbox('Visualización del scorecard',['Ranking score','Gasto vs score','Heatmap proveedor × indicador','Pareto de gasto','Barras de estabilidad'])
    if scv.startswith('Ranking'): fig_sc=px.bar(top_sc.sort_values('Score'),x='Score',y='Proveedor',orientation='h',text_auto='.1f')
    elif scv.startswith('Gasto'): fig_sc=px.bar(top_sc,x='Proveedor',y='Gasto',text='Score',hover_data=['Compras','Materiales','CV'])
    elif scv.startswith('Heatmap'):
        h=top_sc.set_index('Proveedor')[['Score','Compras','Materiales','CV']]; fig_sc=px.imshow(h,aspect='auto',text_auto='.2f')
    elif scv.startswith('Pareto'):
        p=scorecard.sort_values('Gasto',ascending=False).head(20); p['Acum']=p.Gasto.cumsum()/max(p.Gasto.sum(),1)*100; fig_sc=go.Figure([go.Bar(x=p.Proveedor,y=p.Gasto),go.Scatter(x=p.Proveedor,y=p.Acum,yaxis='y2',mode='lines+markers')]); fig_sc.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105]))
    else: fig_sc=px.bar(top_sc.sort_values('CV',ascending=False),x='CV',y='Proveedor',orientation='h')
    fig_sc.update_layout(height=500)
    st.plotly_chart(fig_sc,use_container_width=True)
    explain('El score no premia solo precio: usa evidencia de recurrencia, variedad de materiales y estabilidad histórica.','Crear una primera shortlist de proveedores; no sustituye evaluación de calidad y cumplimiento.')
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
        st.download_button('⬇️ Descargar plan Casas 5–6',plan.to_csv(index=False).encode('utf-8-sig'),'plan_compras_casas_5_6_v7.csv','text/csv')

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
    st.download_button('⬇️ Descargar selección',z.to_csv(index=False).encode('utf-8-sig'),'base_maestra_filtrada_v7.csv','text/csv')

st.divider()
st.caption('Construir Mejor · V7 MASTER DECISION · SIN IMÁGENES · 3 Superbloque + 1 convencional → auditoría → decisión → Should Cost → Casas 5 y 6 · cobertura mínima 95% + regla estructural 23/03.')
