from pathlib import Path
import math, re, html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Construction Intelligence V6",page_icon="🏗️",layout="wide",initial_sidebar_state="expanded")
BASE=Path(__file__).with_name("base_maestra_homologada_2392.csv")
DEFAULT_H1_START=pd.Timestamp("2024-11-01"); DEFAULT_H1_END=pd.Timestamp("2025-03-22")
DEFAULT_H2_START=pd.Timestamp("2025-03-23"); DEFAULT_H2_END=pd.Timestamp("2025-08-31")
DEFAULT_H3_START=pd.Timestamp("2025-09-01"); DEFAULT_H3_END=pd.Timestamp("2026-03-22")
DEFAULT_H4_START=pd.Timestamp("2026-03-23"); DEFAULT_H4_END=pd.Timestamp("2026-08-31")
STAGE_PLAN=[
("Preparación y cimentación",1,3,["Cemento","Arena","Piedra","Varilla"]),
("Estructura",3,8,["Varilla","Cemento","Malla","Concreto"]),
("Mampostería",5,10,["Block","Cemento","Arena"]),
("Cubierta",8,11,["Cubierta","Tornillería","Selladores"]),
("Hidrosanitario",8,13,["PVC","Accesorios","Tubería"]),
("Eléctrico",9,14,["Cable","Conduit","Cajas","Accesorios"]),
("Repellos y preparación",12,16,["Morteros","Repellos","Cemento","Arena"]),
("Cielos y divisiones",14,18,["Gypsum","Perfiles","Tornillería"]),
("Pisos y enchapes",17,20,["Porcelanato","Cerámica","Bondex","Fragüe"]),
("Pintura",18,22,["Pintura","Sellador","Accesorios"]),
("Carpintería y acabados",20,23,["Puertas","Herrajes","Mobiliario"]),
("Sanitarios y cierre",20,24,["Sanitarios","Grifería","Accesorios"]),]

st.markdown("""<style>
:root{color-scheme:light dark}
.stApp{background:var(--background-color);color:var(--text-color)}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1500px}
.hero{padding:25px 28px;border-radius:24px;background:linear-gradient(135deg,color-mix(in srgb,var(--primary-color) 18%,var(--background-color)),color-mix(in srgb,var(--secondary-background-color) 92%,var(--background-color)));border:1px solid color-mix(in srgb,var(--text-color) 14%,transparent);margin-bottom:18px}
.hero .eyebrow{font-size:.76rem;letter-spacing:.18em;text-transform:uppercase;opacity:.66}.hero h1{font-size:2.15rem;margin:.2rem 0 .35rem}.hero p{opacity:.78;margin:0;max-width:940px}
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:10px 0 20px}.kpi,.house-card,.material-card,.rec-card,.explain{background:var(--secondary-background-color);color:var(--text-color);border:1px solid color-mix(in srgb,var(--text-color) 12%,transparent);box-shadow:0 8px 24px color-mix(in srgb,var(--text-color) 7%,transparent)}
.kpi{border-radius:18px;padding:16px 18px}.kpi .label{font-size:.75rem;opacity:.62;text-transform:uppercase;letter-spacing:.08em}.kpi .value{font-size:1.48rem;font-weight:820;margin-top:3px}.kpi .sub{font-size:.8rem;opacity:.62;margin-top:3px}
.house-row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:12px 0 22px}.house-card{position:relative;border-radius:22px;padding:18px 20px;overflow:hidden}.house-card:after{content:"";position:absolute;right:-35px;top:-35px;width:110px;height:110px;border-radius:50%;background:color-mix(in srgb,var(--primary-color) 15%,transparent)}.house-icon{font-size:1.8rem}.house-name{font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;opacity:.62;margin-top:5px}.house-cost{font-size:1.65rem;font-weight:850}.delta-up{color:#e35d54;font-weight:760}.delta-down{color:#31b887;font-weight:760}.delta-flat{opacity:.68;font-weight:760}
.material-card,.rec-card{border-radius:18px;padding:14px 16px;margin-bottom:10px}.material-card .title,.rec-card .supplier{font-weight:820}.material-card .meta,.rec-card .meta{font-size:.82rem;opacity:.63;margin-top:3px}.rec-card .rank{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;opacity:.6}.rec-card .signal{font-size:.84rem;font-weight:760;margin-top:4px}
.explain{border-radius:14px;padding:10px 13px;margin:5px 0 16px;font-size:.86rem;box-shadow:none}.explain b{font-weight:800}.chip{display:inline-block;padding:5px 9px;border-radius:999px;background:color-mix(in srgb,var(--primary-color) 13%,var(--secondary-background-color));font-size:.75rem;margin:2px 3px 2px 0}.sourcebox{background:var(--secondary-background-color);border:1px dashed color-mix(in srgb,var(--text-color) 22%,transparent);border-radius:14px;padding:12px 14px;font-size:.87rem;opacity:.9}
[data-testid="stDataFrame"]{border-radius:16px;overflow:hidden;border:1px solid color-mix(in srgb,var(--text-color) 13%,transparent)}div[data-testid="stMetric"]{background:var(--secondary-background-color);border:1px solid color-mix(in srgb,var(--text-color) 12%,transparent);padding:12px 14px;border-radius:16px}
@media(max-width:900px){.kpi-grid,.house-row{grid-template-columns:1fr}.hero h1{font-size:1.65rem}}
</style>""",unsafe_allow_html=True)

def chart_explain(read,decision):
    st.markdown(f"<div class='explain'><b>Cómo leerlo:</b> {read}<br><b>Qué decisión ayuda a tomar:</b> {decision}</div>",unsafe_allow_html=True)
def money(v): return "—" if pd.isna(v) else f"₡{v:,.0f}".replace(",",".")
def pct(v): return "—" if pd.isna(v) or not np.isfinite(v) else f"{v:+.1f}%"
def clean_text(s):
    s=str(s).lower().replace('ñ','n'); s=re.sub(r'[^a-z0-9/#.x\s]+',' ',s); return re.sub(r'\s+',' ',s).strip()
def extract_size(desc):
    s=clean_text(desc)
    for p in [r'\b\d+(?:\.\d+)?x\d+(?:\.\d+)?(?:x\d+(?:\.\d+)?)?\b',r'\b\d+\s+\d+/\d+\b',r'\b\d+/\d+\b',r'\b\d+\s*mm\b',r'\b\d+\s*cm\b']:
        m=re.search(p,s)
        if m:return m.group(0)
    return ''
def commercial_unit(row):
    d=clean_text(row['Descripcion_original']); mat=clean_text(row['Material_homologado']); prov=clean_text(row['Proveedor']); pres=str(row.get('Presentacion','') or '')
    if pd.notna(row.get('Kg_por_unidad')) and float(row.get('Kg_por_unidad'))>0:return pres
    for word,label in [('paquete','Paquete'),('bolsa','Bolsa'),('caja','Caja'),('rollo','Rollo'),('juego','Juego'),('set','Set')]:
        if word in d:return label
    if 'clavo' in mat and 'epa' in prov:return 'Paquete/bolsa EPA'
    return pres if pres and pres!='nan' else 'Unidad comercial'
def comparable_key(row):
    mat=str(row['Material_homologado']); size=extract_size(row['Descripcion_original']); unit=row['Unidad_comercial']
    if any(k in clean_text(mat) for k in ['clavo','tornillo','perno','arandela','grapa']): return ' · '.join([x for x in [mat,size,unit] if x])
    return f"{mat} · {row['Presentacion']}"


def physical_component(row):
    txt=clean_text(f"{row.get('Material_homologado','')} {row.get('Descripcion_original','')} {row.get('Familia','')}")
    # Melamine furniture: only explicit/strongly related terms.
    if re.search(r'\bmelamina\b|\bmelaminico\b|corte.*melamin|tapacanto|canto pvc|tornillo.*melamin|bisagra.*mueble|corredera.*gaveta',txt):
        return 'Carpintería / muebles de melamina'
    # Front polycarbonate roof and its clearly attributable structure/fixings.
    if 'policarbonato' in txt:
        return 'Cubierta frontal de policarbonato'
    if re.search(r'tubo.*metal|tubo.*hierro|perfil.*metal|perfil.*hierro',txt) and re.search(r'techo|cubierta|policarbonato',txt):
        return 'Cubierta frontal de policarbonato'
    if re.search(r'tornill|fijacion|sellador|silicon',txt) and 'policarbonato' in txt:
        return 'Cubierta frontal de policarbonato'
    if re.search(r'inodoro|sanitario|lavatorio|lavaman|ducha|grifer',txt):
        return 'Baños / aparatos sanitarios'
    if re.search(r'puerta.*vidrio|puerta corred|puerta principal|puerta.*servicio|\bpuerta\b',txt):
        return 'Puertas'
    if re.search(r'\bventana\b',txt):
        return 'Ventanas'
    return 'Otros materiales'

def add_fiscal_columns(d, tax_rate):
    """The consolidated material lines are net of sales tax per user confirmation.
    Tax-inclusive fields are derived estimates using the selected rate."""
    o=d.copy()
    o['Precio_sin_impuesto']=o['Precio_unitario']
    o['Subtotal_sin_impuesto']=o['Total_linea']
    o['Tasa_impuesto_aplicada']=tax_rate
    o['Impuesto_estimado']=o['Subtotal_sin_impuesto']*tax_rate
    o['Precio_con_impuesto']=o['Precio_sin_impuesto']*(1+tax_rate)
    o['Total_con_impuesto']=o['Subtotal_sin_impuesto']+o['Impuesto_estimado']
    o['Estado_impuesto']='Calculado desde precio neto'
    return o

@st.cache_data
def load_data():
    d=pd.read_csv(BASE); d['Fecha']=pd.to_datetime(d['Fecha'],errors='coerce')
    for c in ['Cantidad','Precio_unitario','Total_linea','Kg_por_unidad','Precio_por_kg','Relevancia']:d[c]=pd.to_numeric(d[c],errors='coerce')
    for c in ['Descripcion_original','Material_homologado','Presentacion','Familia','Proveedor','Tipo_registro']:d[c]=d[c].fillna('')
    weight_material=d['Material_homologado'].str.contains(r'bond|cemento|mortero|repello|fragüe|frague|pegamento',case=False,regex=True,na=False)
    for idx in d[d['Kg_por_unidad'].isna() & weight_material].index:
        txt=clean_text(d.at[idx,'Descripcion_original']); m=re.search(r'\b(\d+(?:\.\d+)?)\s*(?:kg|kgs|kls|k)\b',txt)
        if m:
            kg=float(m.group(1)); d.at[idx,'Kg_por_unidad']=kg
            if d.at[idx,'Precio_unitario']>0:d.at[idx,'Precio_por_kg']=d.at[idx,'Precio_unitario']/kg
            if d.at[idx,'Presentacion'] in ('','Unidad'):d.at[idx,'Presentacion']=f'Saco/bolsa {kg:g} kg'
    d['Es_flete']=d['Descripcion_original'].str.contains(r'flete|transporte|acarreo|env[ií]o|entrega',case=False,regex=True,na=False)
    d['Unidad_comercial']=d.apply(commercial_unit,axis=1); d['Comparable']=d.apply(comparable_key,axis=1); d['Componente_vivienda']=d.apply(physical_component,axis=1); return d

def assign_houses(d,h1s,h1e,h2s,h2e,h3s,h3e,h4s,h4e):
    o=d.copy();o['Casa']='Fuera de ventanas'
    o.loc[o.Fecha.between(h1s,h1e),'Casa']='Casa 1'
    o.loc[o.Fecha.between(h2s,h2e),'Casa']='Casa 2'
    o.loc[o.Fecha.between(h3s,h3e),'Casa']='Casa 3'
    o.loc[o.Fecha.between(h4s,h4e),'Casa']='Casa 4'
    return o
def scope_data(d):return d[d.Tipo_registro.isin(['Material permanente','Material/consumible','Consumible de obra','Otro registrado'])].copy()
def latest_trend(g,metric):
    z=g.dropna(subset=['Fecha',metric]).sort_values('Fecha')
    if z.empty:return np.nan,'Sin datos',0.0
    latest=float(z.iloc[-1][metric]); first=float(z.iloc[0][metric]); ch=((latest-first)/first*100) if len(z)>1 and first else 0; sig='Subiendo' if ch>5 else ('Bajando' if ch<-5 else ('Estable' if len(z)>1 else 'Sin tendencia'));return latest,sig,ch
def supplier_stats(x,metric):
    rows=[]
    for p,g in x.groupby('Proveedor'):
        latest,tr,ch=latest_trend(g,metric);rows.append({'Proveedor':p,'Precio_min':g[metric].min(),'Precio_max':g[metric].max(),'Total_gastado':g.Valor_analisis.sum(),'Ultimo_precio':latest,'Tendencia':tr,'Cambio_pct':ch,'Compras':g.Factura.nunique()})
    return pd.DataFrame(rows)
def recipe_base(d):
    perm=d[d.Tipo_registro.isin(['Material permanente','Material/consumible'])].copy()
    core=perm[perm.Casa3_regla_23mar.eq('Sí')].groupby(['Material_homologado','Familia','Presentacion'],as_index=False).agg(Cantidad_base=('Cantidad','sum'),Costo_hist=('Valor_analisis','sum'))
    core['Metodo']='Última casa confirmada desde 23/03/2026'
    used=set(core.Material_homologado)
    other=perm[~perm.Material_homologado.isin(used)].groupby(['Material_homologado','Familia','Presentacion'],as_index=False).agg(Cantidad_total=('Cantidad','sum'),Costo_hist=('Valor_analisis','sum'))
    other['Cantidad_base']=other.Cantidad_total/4
    other['Metodo']='Histórico total ÷ 4 casas'
    other=other[['Material_homologado','Familia','Presentacion','Cantidad_base','Costo_hist','Metodo']]
    r=pd.concat([core,other],ignore_index=True)
    rel=perm.groupby('Material_homologado').Relevancia.min()
    r['Relevancia']=r.Material_homologado.map(rel).fillna(5)
    return r.sort_values(['Relevancia','Costo_hist','Cantidad_base'],ascending=[True,False,False])
def drivers(a,b):
    aa=a.groupby('Material_homologado').Valor_analisis.sum();bb=b.groupby('Material_homologado').Valor_analisis.sum();c=pd.concat([aa.rename('A'),bb.rename('B')],axis=1).fillna(0);c['Delta']=c.B-c.A;c['AbsDelta']=c.Delta.abs();return c.sort_values('AbsDelta',ascending=False)
def signal_text(trend,current,target):
    gap=(current-target)/target*100 if target and target>0 else 0
    if trend=='Subiendo':return '⚡ Negociar pronto',f'El precio viene subiendo. Conviene cerrar cotizaciones antes de que se aleje más del mínimo histórico; brecha actual {gap:.1f}%.'
    if trend=='Bajando':return '🟢 Cotizar antes de cerrar',f'La tendencia es favorable. Compare precios recientes antes de adelantar todo el pedido; brecha al mejor histórico {gap:.1f}%.'
    if gap<=5:return '✅ Buen rango',f'El precio reciente está cerca del mejor nivel histórico; brecha {gap:.1f}%.'
    return '🎯 Negociar',f'El precio está estable, pero existe una brecha de {gap:.1f}% frente al mejor histórico comparable.'
def build_animation(n_houses):
    stages=''.join([f"<div class='stage' style='--d:{i*0.15}s'><span>{i+1}</span><b>{html.escape(s[0])}</b><small>Sem {s[1]}–{s[2]}</small></div>" for i,s in enumerate(STAGE_PLAN)])
    houses=''.join(["<div class='house'><div class='roof'></div><div class='body'><div class='floor f2'></div><div class='floor f1'></div><div class='door'></div><div class='window w1'></div><div class='window w2'></div></div><label>Casa "+str(5+i)+"</label></div>" for i in range(n_houses)])
    components.html(f"""<div id='buildv6'><style>#buildv6{{font-family:system-ui;color:CanvasText;background:Canvas;border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:22px;padding:18px}}.wrap{{display:grid;grid-template-columns:minmax(220px,.7fr) minmax(360px,1.5fr);gap:22px;align-items:center}}.houses{{display:flex;gap:22px;justify-content:center;flex-wrap:wrap}}.house{{width:120px;text-align:center;position:relative;padding-top:40px}}.roof{{width:0;height:0;border-left:66px solid transparent;border-right:66px solid transparent;border-bottom:54px solid color-mix(in srgb,CanvasText 75%,transparent);position:absolute;left:-6px;top:0;animation:drop .65s ease both}}.body{{height:135px;border:4px solid color-mix(in srgb,CanvasText 65%,transparent);border-radius:4px;position:relative;overflow:hidden;background:color-mix(in srgb,Canvas 88%,CanvasText)}}.floor{{position:absolute;left:0;right:0;height:50%;background:color-mix(in srgb,#19b99a 38%,Canvas);transform-origin:bottom;animation:fill 1.2s cubic-bezier(.2,.8,.2,1) both}}.f1{{bottom:0;animation-delay:.25s}}.f2{{top:0;animation-delay:.8s}}.door{{position:absolute;width:25px;height:45px;bottom:0;left:47px;background:Canvas}}.window{{position:absolute;width:22px;height:22px;border:2px solid CanvasText;top:28px;background:color-mix(in srgb,#ffcf57 55%,Canvas)}}.w1{{left:18px}}.w2{{right:18px}}.house label{{display:block;margin-top:8px;font-weight:800}}.timeline{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}.stage{{border:1px solid color-mix(in srgb,CanvasText 13%,transparent);border-radius:12px;padding:8px;opacity:0;transform:translateY(7px);animation:show .45s ease forwards;animation-delay:var(--d)}}.stage span{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:color-mix(in srgb,#19b99a 24%,Canvas);font-size:11px;font-weight:800;margin-right:5px}}.stage b{{font-size:12px}}.stage small{{display:block;opacity:.62;margin-top:4px}}@keyframes fill{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}@keyframes drop{{from{{transform:translateY(-12px);opacity:0}}to{{transform:none;opacity:1}}}}@keyframes show{{to{{opacity:1;transform:none}}}}@media(prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important;transform:none!important}}}}@media(max-width:700px){{.wrap{{grid-template-columns:1fr}}.timeline{{grid-template-columns:repeat(2,1fr)}}}}</style><div class='wrap'><div class='houses'>{houses}</div><div><h3 style='margin:0 0 8px'>Ruta de construcción y abastecimiento</h3><p style='margin:0 0 12px;opacity:.68;font-size:13px'>La animación ilustra cómo el plan de compras acompaña las etapas; no representa avance real.</p><div class='timeline'>{stages}</div></div></div></div>""",height=485,scrolling=False)

df=load_data()
st.markdown("""<div class='hero'><div class='eyebrow'>Construction Intelligence · V6</div><h1>De 4 casas históricas a un plan de compra más inteligente</h1><p>2.392 líneas homologadas, costos con y sin impuesto claramente identificados, receta física por vivienda, tendencias comparables y planificación visual para las próximas Casas 5 y 6.</p></div>""",unsafe_allow_html=True)
with st.sidebar:
    st.header('⚙️ Supuestos y lectura')
    st.caption('Las ventanas de Casa 1–4 son inferidas y editables; el profesional confirmó que el histórico corresponde a 4 casas.')
    h1s=st.date_input('Casa 1 · inicio',DEFAULT_H1_START.date());h1e=st.date_input('Casa 1 · fin',DEFAULT_H1_END.date())
    h2s=st.date_input('Casa 2 · inicio',DEFAULT_H2_START.date());h2e=st.date_input('Casa 2 · fin',DEFAULT_H2_END.date())
    h3s=st.date_input('Casa 3 · inicio',DEFAULT_H3_START.date());h3e=st.date_input('Casa 3 · fin',DEFAULT_H3_END.date())
    h4s=st.date_input('Casa 4 · inicio',DEFAULT_H4_START.date());h4e=st.date_input('Casa 4 · fin',DEFAULT_H4_END.date())
    st.divider()
    tax_pct=st.number_input('Impuesto de ventas para estimación (%)',min_value=0.0,max_value=30.0,value=13.0,step=0.5)
    tax_rate=tax_pct/100
    price_view=st.radio('Mostrar costos',['Costo final con impuesto','Precio sin impuesto'],index=0)
    st.caption('El consolidado recibido está sin impuesto. Cuando se muestra “con impuesto”, el dashboard lo calcula con la tasa seleccionada y lo identifica como estimado.')
    st.divider()
    waste=st.slider('Margen de seguridad Casa 5/6',0,20,7,1)/100
    future_houses=st.radio('Planificar',['Casa 5','Casa 6','Casas 5 + 6'],index=2)
    n_future=2 if future_houses=='Casas 5 + 6' else 1
    st.divider()
    st.caption('23/03/2026: solo arena, block, piedra, cemento y varilla se atribuyen directamente a la última casa histórica (Casa 4).')
df=add_fiscal_columns(df,tax_rate)
value_col='Total_con_impuesto' if price_view=='Costo final con impuesto' else 'Subtotal_sin_impuesto'
unit_price_col='Precio_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_sin_impuesto'
df['Valor_analisis']=df[value_col]
hdf=assign_houses(df,pd.Timestamp(h1s),pd.Timestamp(h1e),pd.Timestamp(h2s),pd.Timestamp(h2e),pd.Timestamp(h3s),pd.Timestamp(h3e),pd.Timestamp(h4s),pd.Timestamp(h4e))
scope=scope_data(hdf)
inh=scope[scope.Casa.isin(['Casa 1','Casa 2','Casa 3','Casa 4'])].copy()
freight=scope[scope.Es_flete & (scope.Valor_analisis>1)].copy()
labels=['✨ Historia ejecutiva','🏠 Anatomía de la casa','🧱 Receta visual','🏪 Material × proveedor','📈 Evolución de precio','🎯 Casas 5 y 6','🔎 Explorador maestro']
if len(freight):labels.insert(4,'🚚 Fletes')
tabs=st.tabs(labels);ti={name:tabs[i] for i,name in enumerate(labels)}
st.markdown(f"<div class='sourcebox'><b>💰 Tratamiento fiscal:</b> el consolidado de materiales está registrado <b>sin impuesto de ventas</b>. Vista activa: <b>{price_view}</b>. Cuando se visualiza costo final, se aplica {tax_pct:.1f}% como estimación y se mantiene separado del precio neto.</div>",unsafe_allow_html=True)

with ti['✨ Historia ejecutiva']:
    costs=inh.groupby('Casa').Valor_analisis.sum().reindex(['Casa 1','Casa 2','Casa 3','Casa 4']).fillna(0)
    c1,c2,c3,c4=costs.tolist()
    d12=(c2/c1-1)*100 if c1 else np.nan;d23=(c3/c2-1)*100 if c2 else np.nan;d34=(c4/c3-1)*100 if c3 else np.nan
    tax_label='Impuesto incluido · estimado' if price_view=='Costo final con impuesto' else 'Sin impuesto'
    st.markdown(f"<div class='explain'><b>Lectura fiscal:</b> Todos los montos de esta vista están en <b>{tax_label}</b>. El consolidado fuente no incluye impuesto.</div>",unsafe_allow_html=True)
    dc=lambda x:'delta-up' if x>0 else ('delta-down' if x<0 else 'delta-flat')
    dt=lambda x:f'{pct(x)} vs anterior' if pd.notna(x) else '—'
    st.markdown(f"<div class='house-row'><div class='house-card'><div class='house-icon'>🏠</div><div class='house-name'>Casa 1</div><div class='house-cost'>{money(c1)}</div><div class='delta-flat'>Base · {tax_label}</div></div><div class='house-card'><div class='house-icon'>🏡</div><div class='house-name'>Casa 2</div><div class='house-cost'>{money(c2)}</div><div class='{dc(d12)}'>{dt(d12)}</div></div><div class='house-card'><div class='house-icon'>🏘️</div><div class='house-name'>Casa 3</div><div class='house-cost'>{money(c3)}</div><div class='{dc(d23)}'>{dt(d23)}</div></div><div class='house-card'><div class='house-icon'>🏠</div><div class='house-name'>Casa 4</div><div class='house-cost'>{money(c4)}</div><div class='{dc(d34)}'>{dt(d34)}</div></div></div>",unsafe_allow_html=True)
    view=st.selectbox('Visualización del costo por casa',['Trayectoria conectada','Burbujas comparativas','Waterfall acumulativo'])
    if view=='Trayectoria conectada':fig=go.Figure(go.Scatter(x=costs.index,y=costs.values,mode='lines+markers+text',text=[money(v) for v in costs],textposition='top center',line=dict(width=8,shape='spline'),marker=dict(size=34,symbol='hexagon')))
    elif view=='Burbujas comparativas':fig=go.Figure(go.Scatter(x=costs.index,y=[1,1,1],mode='markers+text',text=[money(v) for v in costs],textposition='top center',marker=dict(size=np.sqrt(costs.values/costs.max())*105+35)));fig.update_yaxes(visible=False)
    else:fig=go.Figure(go.Waterfall(x=['Casa 1','Cambio 1→2','Cambio 2→3'],measure=['absolute','relative','relative'],y=[c1,c2-c1,c3-c2],text=[money(c1),money(c2-c1),money(c3-c2)],textposition='outside'))
    fig.update_layout(title='Tendencia del costo de operación por casa',height=430,template='streamlit',showlegend=False);st.plotly_chart(fig,use_container_width=True);chart_explain('Observe dirección y magnitud del cambio entre casas.','Saber si la nueva casa está costando más o menos y cuánto.')
    comp=st.segmented_control('Comparación de drivers',['Casa 1 → Casa 2','Casa 2 → Casa 3','Casa 3 → Casa 4'],default='Casa 3 → Casa 4')
    if comp=='Casa 1 → Casa 2': a,b=inh[inh.Casa.eq('Casa 1')],inh[inh.Casa.eq('Casa 2')]
    elif comp=='Casa 2 → Casa 3': a,b=inh[inh.Casa.eq('Casa 2')],inh[inh.Casa.eq('Casa 3')]
    else: a,b=inh[inh.Casa.eq('Casa 3')],inh[inh.Casa.eq('Casa 4')]
    drv=drivers(a,b).head(18).reset_index();dv=st.selectbox('Visualización de drivers',['Waterfall de impacto','Treemap de variación','Burbujas de impacto'])
    if dv=='Waterfall de impacto':q=drv.head(12);fig=go.Figure(go.Waterfall(x=q.Material_homologado,measure=['relative']*len(q),y=q.Delta,text=[money(v) for v in q.Delta],textposition='outside'))
    elif dv=='Treemap de variación':q=drv.copy();q['Dirección']=np.where(q.Delta>=0,'Aumenta costo','Reduce costo');fig=px.treemap(q,path=['Dirección','Material_homologado'],values='AbsDelta',color='Delta',color_continuous_scale='RdYlGn_r')
    else:q=drv.copy();fig=px.scatter(q,x='Delta',y='AbsDelta',size='AbsDelta',hover_name='Material_homologado',color=np.where(q.Delta>=0,'Aumenta','Ahorra'))
    fig.update_layout(title=f'Drivers · {comp}',height=520,template='streamlit');st.plotly_chart(fig,use_container_width=True);chart_explain('Mayor tamaño o desplazamiento = mayor efecto en la diferencia. Positivo aumenta costo; negativo reduce.','Priorizar materiales donde realmente se explica la variación.')
    st.markdown("<div class='sourcebox'><b>Superbloque:</b> permanece separado del block convencional porque sus facturas pueden incluir un sistema constructivo con acero y otros componentes.</div>",unsafe_allow_html=True)


with ti['🏠 Anatomía de la casa']:
    st.subheader('🏠 Receta física estándar por vivienda')
    st.caption('Esta estructura sirve para interpretar las facturas: un componente puede aparecer como producto terminado o como varios insumos.')
    profile = pd.DataFrame([
        ['Planta baja','Cocina',1,'Incluye 1 mueble de melamina'],
        ['Planta baja','Sala',1,'Área social'],
        ['Planta baja','Patio',1,'Con acceso por puerta de vidrio de 3 hojas'],
        ['Planta baja','Gradas',1,'Conexión a planta alta'],
        ['Planta baja','Puerta principal',1,'Acceso principal'],
        ['Planta baja','Puerta de vidrio 3 hojas',1,'Salida al patio'],
        ['Planta baja','Puerta de servicio sanitario',1,'Medio baño'],
        ['Planta baja','Medio baño',1,'1 sanitario + 1 lavatorio'],
        ['Planta alta','Dormitorios',2,'1 mueble de melamina por dormitorio'],
        ['Planta alta','Baño completo',1,'Sanitario + lavatorio + ducha'],
        ['Planta alta','Ventanas dormitorios',2,'1 por habitación'],
        ['Planta alta','Ventana baño',1,'Ventana adicional'],
        ['Frente','Cubierta de policarbonato',1,'Sobre estructura de tubos metálicos'],
    ], columns=['Nivel','Componente','Cantidad por casa','Interpretación'])
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Dormitorios','2');c2.metric('Baños','1 completo + 1 medio');c3.metric('Muebles melamina','3');c4.metric('Ventanas planta alta','3')
    av=st.selectbox('Visualización',['Mapa de componentes','Treemap de la vivienda','Tabla de receta física'])
    if av=='Treemap de la vivienda':
        fig=px.treemap(profile,path=['Nivel','Componente'],values='Cantidad por casa',hover_data=['Interpretación'])
        fig.update_layout(height=520,template='streamlit');st.plotly_chart(fig,use_container_width=True)
    elif av=='Tabla de receta física':
        st.dataframe(profile,use_container_width=True,hide_index=True)
    else:
        nodes=['Casa estándar','Planta baja','Planta alta','Frente']+profile.Componente.tolist()
        src=[];tgt=[];val=[]
        for _,r in profile.iterrows():
            parent=r.Nivel
            src.append(nodes.index(parent));tgt.append(nodes.index(r.Componente));val.append(float(r['Cantidad por casa']))
        for parent in ['Planta baja','Planta alta','Frente']:
            src.append(0);tgt.append(nodes.index(parent));val.append(float(profile.loc[profile.Nivel.eq(parent),'Cantidad por casa'].sum()))
        fig=go.Figure(go.Sankey(node=dict(label=nodes,pad=14,thickness=16),link=dict(source=src,target=tgt,value=val)))
        fig.update_layout(height=560,template='streamlit');st.plotly_chart(fig,use_container_width=True)
    chart_explain('La vivienda se descompone en espacios y componentes físicos repetibles.','Validar si las compras históricas tienen sentido para 4 casas y construir una receta más confiable para Casas 5 y 6.')
    st.markdown("<div class='explain'><b>Melamina:</b> se consolida desde láminas/tableros, cortes y herrajes claramente atribuibles; no se exige una línea llamada “mueble”.<br><b>Cubierta frontal:</b> se busca policarbonato y, cuando la descripción lo respalda, estructura metálica, fijaciones y selladores relacionados.</div>",unsafe_allow_html=True)
    comp_hist=scope[scope.Componente_vivienda.ne('Otros materiales')].groupby('Componente_vivienda',as_index=False).agg(Lineas=('Linea_id','count'),Costo=('Valor_analisis','sum'),Cantidad=('Cantidad','sum')).sort_values('Costo',ascending=False)
    if not comp_hist.empty:
        st.subheader('Componentes identificados en las facturas')
        fig=px.scatter(comp_hist,x='Lineas',y='Costo',size='Cantidad',hover_name='Componente_vivienda')
        fig.update_layout(height=440,template='streamlit');st.plotly_chart(fig,use_container_width=True)
        chart_explain('Cada burbuja resume líneas que pudieron asociarse con un componente físico.','Detectar qué partes de la vivienda ya pueden costearse de forma consolidada y dónde falta evidencia.')

with ti['🧱 Receta visual']:
    rec=recipe_base(hdf);st.subheader('🧱 Receta estimada de una casa ~100 m² / 2 plantas');rv=st.selectbox('Visualización de la receta',['Sunburst por familia','Treemap de costo','Mapa cantidad × costo'])
    if rv=='Mapa cantidad × costo':q=rec.head(35).copy();q['Peso']=np.log1p(q.Cantidad_base.clip(lower=0))*np.log1p(q.Costo_hist.clip(lower=0));fig=px.scatter(q,x='Cantidad_base',y='Costo_hist',size='Peso',color='Familia',hover_name='Material_homologado',hover_data=['Presentacion','Metodo'])
    else:q=rec.groupby(['Familia','Material_homologado'],as_index=False).agg(Costo=('Costo_hist','sum'));fig=px.sunburst(q,path=['Familia','Material_homologado'],values='Costo') if rv.startswith('Sunburst') else px.treemap(q,path=['Familia','Material_homologado'],values='Costo')
    fig.update_layout(height=550,template='streamlit');st.plotly_chart(fig,use_container_width=True);chart_explain('Una zona/burbuja mayor indica más impacto económico o cantidad.','Identificar materiales que requieren mayor control y planificación.')
    st.markdown('### 🗓️ Ruta de abastecimiento');scale=st.segmented_control('Escala',['Semanas','Meses'],default='Semanas')
    for name,a,b,mats in STAGE_PLAN:
        if scale=='Meses':a,b=(a-1)//4+1,(b-1)//4+1
        chips=''.join(f"<span class='chip'>{m}</span>" for m in mats);st.markdown(f"<div class='material-card'><div class='title'>{name}</div><div class='meta'>{'Semana' if scale=='Semanas' else 'Mes'} {a} → {b}</div><div style='margin-top:8px'>{chips}</div></div>",unsafe_allow_html=True)

with ti['🏪 Material × proveedor']:
    st.subheader('🏪 Comparación material × proveedor');st.caption('Solo MIN, MAX y TOTAL GASTADO. Sin promedio ni mediana.')
    valid=scope[scope.Precio_unitario>0].copy();order=(valid.groupby('Material_homologado').agg(Cantidad=('Cantidad','sum'),Relevancia=('Relevancia','min'),Gasto=('Total_linea','sum')).sort_values(['Relevancia','Cantidad','Gasto'],ascending=[True,False,False]).index.tolist());mat=st.selectbox('Material',order);comps=valid.loc[valid.Material_homologado.eq(mat),'Comparable'].value_counts().index.tolist();ck=st.selectbox('Producto/presentación comparable',comps);x=valid[(valid.Material_homologado.eq(mat))&(valid.Comparable.eq(ck))].copy();usekg=x.Precio_por_kg.notna().any();mode=st.segmented_control('Comparar por',['Precio por kg','Precio por presentación'],default='Precio por kg') if usekg else 'Precio por presentación';metric='Precio_por_kg' if mode=='Precio por kg' else 'Precio_unitario';x=x[x[metric].notna()];ss=supplier_stats(x,metric).sort_values('Precio_min');vv=st.selectbox('Visualización',['Dumbbell MIN ↔ MAX','Burbujas: rango y gasto','Heatmap MIN/MAX'])
    if ss.empty:st.info('No hay datos comparables.')
    else:
        if vv.startswith('Dumbbell'):
            fig=go.Figure()
            for _,r in ss.iterrows():fig.add_trace(go.Scatter(x=[r.Precio_min,r.Precio_max],y=[r.Proveedor,r.Proveedor],mode='lines',line=dict(width=9),showlegend=False,hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=ss.Precio_min,y=ss.Proveedor,mode='markers',marker=dict(size=15,symbol='circle'),name='Mínimo'));fig.add_trace(go.Scatter(x=ss.Precio_max,y=ss.Proveedor,mode='markers',marker=dict(size=15,symbol='diamond'),name='Máximo'))
        elif vv.startswith('Burbujas'):ss['Rango']=ss.Precio_max-ss.Precio_min;fig=px.scatter(ss,x='Precio_min',y='Precio_max',size='Total_gastado',hover_name='Proveedor',hover_data=['Total_gastado','Rango'])
        else:fig=px.imshow(ss.set_index('Proveedor')[['Precio_min','Precio_max']],aspect='auto',text_auto='.0f')
        fig.update_layout(title=f'{mat} · {ck}',height=max(420,120+55*len(ss)),template='streamlit');st.plotly_chart(fig,use_container_width=True);chart_explain('Compare el mejor y peor precio pagado por proveedor; el gasto total da contexto al peso del proveedor.','Definir rango de negociación sin depender de promedios.')

with ti['📈 Evolución de precio']:
    st.subheader('📈 Evolución histórica del precio');st.caption('La unidad comercial se valida primero. Clavos EPA se tratan como paquete/bolsa, no como pieza.')
    mats=(scope[scope.Precio_unitario>0].groupby('Material_homologado').Cantidad.sum().sort_values(ascending=False).index.tolist());mat=st.selectbox('Material',mats,key='tm');comps=scope.loc[(scope.Material_homologado.eq(mat))&(scope.Precio_unitario>0),'Comparable'].value_counts().index.tolist();ck=st.selectbox('Producto/presentación comparable',comps,key='tc');x=scope[(scope.Material_homologado.eq(mat))&(scope.Comparable.eq(ck))&(scope.Precio_unitario>0)&scope.Fecha.notna()].copy();usekg=x.Precio_por_kg.notna().any();mode=st.segmented_control('Métrica',['₡ por kg','₡ por presentación'],default='₡ por kg') if usekg else '₡ por presentación';metric=('Precio_por_kg_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_por_kg') if mode=='₡ por kg' else unit_price_col;x=x[x[metric].notna()].sort_values('Fecha');tv=st.selectbox('Visualización',['Línea temporal por proveedor','Small multiples','Puntos + rango histórico'])
    if tv=='Small multiples':fig=px.line(x,x='Fecha',y=metric,facet_row='Proveedor',markers=True,height=max(430,220*x.Proveedor.nunique()))
    elif tv.startswith('Puntos'):fig=px.scatter(x,x='Fecha',y=metric,color='Proveedor',size=np.maximum(x.Cantidad.fillna(1),1),hover_data=['Descripcion_original','Unidad_comercial'])
    else:fig=px.line(x,x='Fecha',y=metric,color='Proveedor',markers=True)
    fig.update_layout(title=f'Pulso de precio · {ck}',height=540,template='streamlit');st.plotly_chart(fig,use_container_width=True);chart_explain('Cada punto es una compra comparable. La pendiente revela si el precio sube, baja o se mantiene.','Decidir si comprar pronto, negociar o esperar una nueva cotización.')
    ss=supplier_stats(x,metric).sort_values('Ultimo_precio');cols=st.columns(min(3,max(1,len(ss))))
    for i,(_,r) in enumerate(ss.iterrows()):
        icon='📈' if r.Tendencia=='Subiendo' else ('📉' if r.Tendencia=='Bajando' else '➖')
        with cols[i%len(cols)]:st.markdown(f"<div class='rec-card'><div class='rank'>{r.Proveedor}</div><div class='supplier'>{money(r.Ultimo_precio)}</div><div class='signal'>{icon} {r.Tendencia} · {pct(r.Cambio_pct)}</div><div class='meta'>MIN {money(r.Precio_min)} · MAX {money(r.Precio_max)}</div></div>",unsafe_allow_html=True)

if '🚚 Fletes' in ti:
    with ti['🚚 Fletes']:
        st.subheader('🚚 Flete y costo puesto en obra');fh=freight[freight.Casa.isin(['Casa 1','Casa 2','Casa 3','Casa 4'])].copy();st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Flete identificado</div><div class='value'>{money(freight.Valor_analisis.sum())}</div></div><div class='kpi'><div class='label'>Líneas</div><div class='value'>{len(freight)}</div></div><div class='kpi'><div class='label'>Proveedores</div><div class='value'>{freight.Proveedor.nunique()}</div></div><div class='kpi'><div class='label'>Peso sobre gasto</div><div class='value'>{freight.Valor_analisis.sum()/scope.Valor_analisis.sum()*100:.1f}%</div></div></div>",unsafe_allow_html=True);fv=st.selectbox('Visualización',['Sunburst casa → proveedor','Treemap por proveedor','Burbujas por cargo'])
        if fv.startswith('Sunburst'):fig=px.sunburst(fh,path=['Casa','Proveedor'],values='Valor_analisis')
        elif fv.startswith('Treemap'):fig=px.treemap(freight,path=['Proveedor','Descripcion_original'],values='Valor_analisis')
        else:fig=px.scatter(freight,x='Fecha',y='Valor_analisis',size='Valor_analisis',color='Proveedor',hover_name='Descripcion_original')
        fig.update_layout(height=520,template='streamlit');st.plotly_chart(fig,use_container_width=True);chart_explain('El tamaño representa cuánto se pagó en transporte.','Comparar costo puesto en obra y oportunidades de consolidación.')

with ti['🎯 Casas 5 y 6']:
    st.subheader(f'🎯 Centro de planificación · {future_houses}');st.caption('Cuánto comprar, cuándo, dónde cotizar y qué significa la evolución del precio.');rec=recipe_base(hdf);rec['Cantidad_meta']=rec.Cantidad_base*(1+waste)*n_future;cand=rec.sort_values(['Relevancia','Costo_hist'],ascending=[True,False]).head(35);rows=[]
    for _,r in cand.iterrows():
        x=scope[(scope.Material_homologado.eq(r.Material_homologado))&(scope.Presentacion.eq(r.Presentacion))&(scope.Precio_unitario>0)].copy()
        if x.empty:continue
        metric=('Precio_por_kg_con_impuesto' if price_view=='Costo final con impuesto' else 'Precio_por_kg') if x.Precio_por_kg.notna().any() else unit_price_col;x=x[x[metric].notna()];ss=supplier_stats(x,metric)
        if ss.empty:continue
        pmin,pmax=ss.Ultimo_precio.min(),ss.Ultimo_precio.max();span=max(pmax-pmin,1);ss['score']=.58*((ss.Ultimo_precio-pmin)/span)+.27*(ss.Cambio_pct.clip(-30,30)/60+.5)-.15*(np.minimum(ss.Compras,5)/5);ss=ss.sort_values('score');f=ss.iloc[0];s=ss.iloc[1] if len(ss)>1 else None;target=ss.Precio_min.min();action,interpret=signal_text(f.Tendencia,f.Ultimo_precio,target);rows.append({**r.to_dict(),'Proveedor_1':f.Proveedor,'Ultimo_1':f.Ultimo_precio,'Tendencia_1':f.Tendencia,'Cambio_1':f.Cambio_pct,'Proveedor_2':s.Proveedor if s is not None else '—','Ultimo_2':s.Ultimo_precio if s is not None else np.nan,'Precio_meta':target,'Metrica':'₡/kg' if metric=='Precio_por_kg' else '₡/presentación','Accion':action,'Interpretacion':interpret})
    plan=pd.DataFrame(rows);build_animation(n_future)
    if plan.empty:st.info('No hay suficientes datos para construir recomendaciones.')
    else:
        risky=(plan.Tendencia_1=='Subiendo').sum();st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Materiales priorizados</div><div class='value'>{len(plan)}</div></div><div class='kpi'><div class='label'>Tendencia al alza</div><div class='value'>{risky}</div><div class='sub'>Negociar primero</div></div><div class='kpi'><div class='label'>Margen</div><div class='value'>{waste*100:.0f}%</div></div><div class='kpi'><div class='label'>Casas</div><div class='value'>{n_future}</div></div></div>",unsafe_allow_html=True);material=st.selectbox('Explorar material',plan.Material_homologado.tolist());r=plan[plan.Material_homologado.eq(material)].iloc[0];icon='📈' if r.Tendencia_1=='Subiendo' else ('📉' if r.Tendencia_1=='Bajando' else '➖');c1,c2,c3=st.columns(3)
        with c1:st.markdown(f"<div class='rec-card'><div class='rank'>Cantidad objetivo</div><div class='supplier'>{r.Cantidad_meta:,.1f}</div><div class='meta'>{r.Presentacion} · incluye {waste*100:.0f}% seguridad</div></div>",unsafe_allow_html=True)
        with c2:st.markdown(f"<div class='rec-card'><div class='rank'>🥇 Primera opción</div><div class='supplier'>{r.Proveedor_1}</div><div class='signal'>{icon} {r.Tendencia_1} · {pct(r.Cambio_1)}</div><div class='meta'>Último {money(r.Ultimo_1)} · {r.Metrica}</div></div>",unsafe_allow_html=True)
        with c3:st.markdown(f"<div class='rec-card'><div class='rank'>🎯 Meta</div><div class='supplier'>{money(r.Precio_meta)}</div><div class='meta'>{r.Metrica} · mínimo comparable</div></div>",unsafe_allow_html=True)
        st.markdown(f"<div class='explain'><b>{r.Accion}</b><br>{r.Interpretacion}<br><b>Alternativa:</b> {r.Proveedor_2} · último {money(r.Ultimo_2)}.</div>",unsafe_allow_html=True);pv=st.selectbox('Visualización del plan',['Radar de negociación','Sankey material → proveedor','Mapa de urgencia'])
        if pv=='Radar de negociación':q=plan.copy();q['Brecha']=q.Ultimo_1-q.Precio_meta;fig=px.scatter(q,x='Cantidad_meta',y='Brecha',size='Costo_hist',color='Tendencia_1',hover_name='Material_homologado',hover_data=['Proveedor_1','Presentacion','Metrica'])
        elif pv.startswith('Sankey'):
            q=plan.head(18);mats=q.Material_homologado.tolist();provs=list(dict.fromkeys(q.Proveedor_1.tolist()));labs=mats+provs;src=[];tgt=[];val=[]
            for _,z in q.iterrows():src.append(labs.index(z.Material_homologado));tgt.append(labs.index(z.Proveedor_1));val.append(max(float(z.Costo_hist),1))
            fig=go.Figure(go.Sankey(node=dict(label=labs,pad=12,thickness=16),link=dict(source=src,target=tgt,value=val)))
        else:q=plan.copy();q['Urgencia']=np.where(q.Tendencia_1.eq('Subiendo'),3,np.where(q.Tendencia_1.eq('Estable'),2,1));fig=px.scatter(q,x='Urgencia',y='Cantidad_meta',size='Costo_hist',color='Tendencia_1',hover_name='Material_homologado',hover_data=['Proveedor_1','Precio_meta'])
        fig.update_layout(height=560,template='streamlit',title='Plan de compra priorizado');st.plotly_chart(fig,use_container_width=True);chart_explain('Tamaño = impacto económico; tendencia, brecha y volumen indican riesgo u oportunidad.','Ordenar cotizaciones y negociaciones por prioridad real.');st.download_button('⬇️ Descargar plan',plan.to_csv(index=False).encode('utf-8-sig'),'plan_compras_casas_5_6_v6.csv','text/csv')

with ti['🔎 Explorador maestro']:
    st.subheader('🔎 Explorador maestro');c1,c2,c3,c4=st.columns(4);c1.metric('Líneas',f'{len(df):,}');c2.metric('Materiales',df.Material_homologado.nunique());c3.metric('Proveedores',df.Proveedor.nunique());c4.metric('Pendientes manuales','0');search=st.text_input('🔍 Buscar');a,b,c=st.columns(3)
    with a:fam=st.multiselect('Familia',sorted(df.Familia.dropna().unique()))
    with b:prov=st.multiselect('Proveedor',sorted(df.Proveedor.dropna().unique()))
    with c:typ=st.multiselect('Tipo',sorted(df.Tipo_registro.dropna().unique()))
    z=df.copy()
    if fam:z=z[z.Familia.isin(fam)]
    if prov:z=z[z.Proveedor.isin(prov)]
    if typ:z=z[z.Tipo_registro.isin(typ)]
    if search:q=re.escape(search);z=z[z.Material_homologado.str.contains(q,case=False,regex=True,na=False)|z.Descripcion_original.str.contains(q,case=False,regex=True,na=False)|z.Proveedor.str.contains(q,case=False,regex=True,na=False)|z.Factura.astype(str).str.contains(q,case=False,regex=True,na=False)]
    st.markdown(f"<div class='explain'><b>{len(z):,}</b> registros. La columna <b>Unidad comercial</b> evita mezclar paquetes con piezas. Los campos fiscales distinguen precio neto, impuesto estimado y costo final.</div>",unsafe_allow_html=True);cols=['Fecha','Proveedor','Factura','Material_homologado','Descripcion_original','Cantidad','Presentacion','Unidad_comercial','Comparable','Componente_vivienda','Precio_sin_impuesto','Impuesto_estimado','Precio_con_impuesto','Subtotal_sin_impuesto','Total_con_impuesto','Estado_impuesto','Precio_por_kg','Familia','Tipo_registro','Confianza_homologacion'];st.dataframe(z[cols].sort_values('Fecha',ascending=False),use_container_width=True,hide_index=True,height=530);st.download_button('⬇️ Descargar selección',z.to_csv(index=False).encode('utf-8-sig'),'base_maestra_filtrada_v6.csv','text/csv')
st.divider();st.caption('V6 · Base homologada 2.392 líneas · Light/Dark · Presentaciones comerciales comparables · Superbloque como sistema constructivo.')
