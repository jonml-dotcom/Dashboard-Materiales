from pathlib import Path
import math, re, html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Construir Mejor",page_icon="🏗️",layout="wide",initial_sidebar_state="expanded")
HERE=Path(__file__).resolve().parent
BASE=HERE/"base_maestra_homologada_2392.csv"
ALLOC=HERE/"asignacion_auditada_4_casas.csv"
REC_SB=HERE/"receta_superbloque_auditada.csv"
REC_CONV=HERE/"receta_convencional_auditada.csv"
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
    d['Unidad_comercial']=d.apply(commercial_unit,axis=1); d['Comparable']=d.apply(comparable_key,axis=1); return d

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
        latest,tr,ch=latest_trend(g,metric);rows.append({'Proveedor':p,'Precio_min':g[metric].min(),'Precio_max':g[metric].max(),'Total_gastado':g.Total_linea.sum(),'Ultimo_precio':latest,'Tendencia':tr,'Cambio_pct':ch,'Compras':g.Factura.nunique()})
    return pd.DataFrame(rows)
def recipe_base(d):
    perm=d[d.Tipo_registro.isin(['Material permanente','Material/consumible'])].copy();core=perm[perm.Casa3_regla_23mar.eq('Sí')].groupby(['Material_homologado','Familia','Presentacion'],as_index=False).agg(Cantidad_base=('Cantidad','sum'),Costo_hist=('Total_linea','sum'));core['Metodo']='Casa 4 · cantidad real';used=set(core.Material_homologado);other=perm[~perm.Material_homologado.isin(used)].groupby(['Material_homologado','Familia','Presentacion'],as_index=False).agg(Cantidad_total=('Cantidad','sum'),Costo_hist=('Total_linea','sum'));other['Cantidad_base']=other.Cantidad_total/4;other['Metodo']='Histórico total ÷ 4';other=other[['Material_homologado','Familia','Presentacion','Cantidad_base','Costo_hist','Metodo']];r=pd.concat([core,other],ignore_index=True);rel=perm.groupby('Material_homologado').Relevancia.min();r['Relevancia']=r.Material_homologado.map(rel).fillna(5);return r.sort_values(['Relevancia','Costo_hist','Cantidad_base'],ascending=[True,False,False])
def drivers(a,b):
    aa=a.groupby('Material_homologado').Total_linea.sum();bb=b.groupby('Material_homologado').Total_linea.sum();c=pd.concat([aa.rename('A'),bb.rename('B')],axis=1).fillna(0);c['Delta']=c.B-c.A;c['AbsDelta']=c.Delta.abs();return c.sort_values('AbsDelta',ascending=False)
def signal_text(trend,current,target):
    gap=(current-target)/target*100 if target and target>0 else 0
    if trend=='Subiendo':return '⚡ Negociar pronto',f'El precio viene subiendo. Conviene cerrar cotizaciones antes de que se aleje más del mínimo histórico; brecha actual {gap:.1f}%.'
    if trend=='Bajando':return '🟢 Cotizar antes de cerrar',f'La tendencia es favorable. Compare precios recientes antes de adelantar todo el pedido; brecha al mejor histórico {gap:.1f}%.'
    if gap<=5:return '✅ Buen rango',f'El precio reciente está cerca del mejor nivel histórico; brecha {gap:.1f}%.'
    return '🎯 Negociar',f'El precio está estable, pero existe una brecha de {gap:.1f}% frente al mejor histórico comparable.'
def build_animation(n_houses):
    stages=''.join([f"<div class='stage' style='--d:{i*0.15}s'><span>{i+1}</span><b>{html.escape(s[0])}</b><small>Sem {s[1]}–{s[2]}</small></div>" for i,s in enumerate(STAGE_PLAN)])
    houses=''.join(["<div class='house'><div class='roof'></div><div class='body'><div class='floor f2'></div><div class='floor f1'></div><div class='door'></div><div class='window w1'></div><div class='window w2'></div></div><label>Casa "+str(4+i)+"</label></div>" for i in range(n_houses)])
    components.html(f"""<div id='buildv5'><style>#buildv5{{font-family:system-ui;color:CanvasText;background:Canvas;border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:22px;padding:18px}}.wrap{{display:grid;grid-template-columns:minmax(220px,.7fr) minmax(360px,1.5fr);gap:22px;align-items:center}}.houses{{display:flex;gap:22px;justify-content:center;flex-wrap:wrap}}.house{{width:120px;text-align:center;position:relative;padding-top:40px}}.roof{{width:0;height:0;border-left:66px solid transparent;border-right:66px solid transparent;border-bottom:54px solid color-mix(in srgb,CanvasText 75%,transparent);position:absolute;left:-6px;top:0;animation:drop .65s ease both}}.body{{height:135px;border:4px solid color-mix(in srgb,CanvasText 65%,transparent);border-radius:4px;position:relative;overflow:hidden;background:color-mix(in srgb,Canvas 88%,CanvasText)}}.floor{{position:absolute;left:0;right:0;height:50%;background:color-mix(in srgb,#19b99a 38%,Canvas);transform-origin:bottom;animation:fill 1.2s cubic-bezier(.2,.8,.2,1) both}}.f1{{bottom:0;animation-delay:.25s}}.f2{{top:0;animation-delay:.8s}}.door{{position:absolute;width:25px;height:45px;bottom:0;left:47px;background:Canvas}}.window{{position:absolute;width:22px;height:22px;border:2px solid CanvasText;top:28px;background:color-mix(in srgb,#ffcf57 55%,Canvas)}}.w1{{left:18px}}.w2{{right:18px}}.house label{{display:block;margin-top:8px;font-weight:800}}.timeline{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}.stage{{border:1px solid color-mix(in srgb,CanvasText 13%,transparent);border-radius:12px;padding:8px;opacity:0;transform:translateY(7px);animation:show .45s ease forwards;animation-delay:var(--d)}}.stage span{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:color-mix(in srgb,#19b99a 24%,Canvas);font-size:11px;font-weight:800;margin-right:5px}}.stage b{{font-size:12px}}.stage small{{display:block;opacity:.62;margin-top:4px}}@keyframes fill{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}@keyframes drop{{from{{transform:translateY(-12px);opacity:0}}to{{transform:none;opacity:1}}}}@keyframes show{{to{{opacity:1;transform:none}}}}@media(prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important;transform:none!important}}}}@media(max-width:700px){{.wrap{{grid-template-columns:1fr}}.timeline{{grid-template-columns:repeat(2,1fr)}}}}</style><div class='wrap'><div class='houses'>{houses}</div><div><h3 style='margin:0 0 8px'>Ruta de construcción y abastecimiento</h3><p style='margin:0 0 12px;opacity:.68;font-size:13px'>La animación ilustra cómo el plan de compras acompaña las etapas; no representa avance real.</p><div class='timeline'>{stages}</div></div></div></div>""",height=485,scrolling=False)

df=load_data()
audit_alloc=pd.read_csv(ALLOC)
audit_alloc['Costo_asignado']=pd.to_numeric(audit_alloc['Costo_asignado'],errors='coerce').fillna(0)
audit_alloc['Cantidad_asignada']=pd.to_numeric(audit_alloc['Cantidad_asignada'],errors='coerce').fillna(0)
rec_sb=pd.read_csv(REC_SB)
rec_conv=pd.read_csv(REC_CONV)
audit_costs=audit_alloc.groupby('Casa').Costo_asignado.sum().reindex(['Casa 1','Casa 2','Casa 3','Casa 4']).fillna(0)
H4_PENDING_DETAIL={
    'Piso + sanitarios':1128617.92,
    'Muebles de melamina':1121373.18,
    'Puertas y ventanas':484024.70,
    'Policarbonato':597101.73,
    'Zacate':131727.43
}
H4_PENDING_TOTAL=sum(H4_PENDING_DETAIL.values())
H4_EXECUTED=float(audit_costs.loc['Casa 4'])
H4_PROJECTED=H4_EXECUTED+H4_PENDING_TOTAL
st.markdown("""<div class='hero'><div class='eyebrow'>CONSTRUIR MEJOR</div><h1>La receta, el costo y la oportunidad detrás de cada casa.</h1><p>De las compras históricas a una receta clara para construir mejor las próximas viviendas.</p></div>""",unsafe_allow_html=True)
with st.sidebar:
    st.header('⚙️ Plan de compra')
    h1s=DEFAULT_H1_START.date();h1e=DEFAULT_H1_END.date();h2s=DEFAULT_H2_START.date();h2e=DEFAULT_H2_END.date();h3s=DEFAULT_H3_START.date();h3e=DEFAULT_H3_END.date();h4s=DEFAULT_H4_START.date();h4e=DEFAULT_H4_END.date();waste=st.slider('Margen de seguridad',0,20,7,1)/100;future_houses=st.radio('Planificar',['Casa 5','Casa 6','Casas 5 + 6'],index=2);n_future=2 if future_houses=='Casas 5 + 6' else 1;st.divider();st.caption('Receta: materiales comunes ÷ 4. Estructura de Casa 4: cantidades reales desde 23/03/2026.')
hdf=assign_houses(df,pd.Timestamp(h1s),pd.Timestamp(h1e),pd.Timestamp(h2s),pd.Timestamp(h2e),pd.Timestamp(h3s),pd.Timestamp(h3e),pd.Timestamp(h4s),pd.Timestamp(h4e));scope=scope_data(hdf);inh=scope[scope.Casa.isin(['Casa 1','Casa 2','Casa 3','Casa 4'])].copy();freight=scope[scope.Es_flete & (scope.Total_linea>1)].copy()
labels=['✨ Historia ejecutiva','🧱 Receta visual','🏪 Material × proveedor','📈 Evolución de precio','🎯 Casas 5 y 6','🔎 Explorador maestro']
if len(freight):labels.insert(4,'🚚 Fletes')
tabs=st.tabs(labels);ti={name:tabs[i] for i,name in enumerate(labels)}

with ti['✨ Historia ejecutiva']:
    house_order=['Casa 1','Casa 2','Casa 3','Casa 4']
    systems={'Casa 1':'Superbloque','Casa 2':'Superbloque','Casa 3':'Superbloque','Casa 4':'Block convencional'}
    costs=audit_costs.copy()
    c1,c2,c3,c4=costs.tolist()
    projected=pd.Series([c1,c2,c3,H4_PROJECTED],index=house_order)
    d12=(c2/c1-1)*100 if c1 else np.nan;d23=(c3/c2-1)*100 if c2 else np.nan
    st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Casa 1 terminada</div><div class='value'>{money(c1)}</div><div class='sub'>Superbloque</div></div><div class='kpi'><div class='label'>Casa 2 terminada</div><div class='value'>{money(c2)}</div><div class='sub'>{d12:+.1f}% vs Casa 1</div></div><div class='kpi'><div class='label'>Casa 3 terminada</div><div class='value'>{money(c3)}</div><div class='sub'>{d23:+.1f}% vs Casa 2</div></div><div class='kpi'><div class='label'>Casa 4 ejecutado</div><div class='value'>{money(c4)}</div><div class='sub'>En proceso · NO costo final</div></div></div>",unsafe_allow_html=True)
    st.markdown(f"""<div class='house-row'>
    <div class='house-card'><div class='house-icon'>🏠</div><div class='house-name'>Casa 1 · Superbloque</div><div class='house-cost'>{money(c1)}</div><div class='delta-flat'>Terminada</div></div>
    <div class='house-card'><div class='house-icon'>🏡</div><div class='house-name'>Casa 2 · Superbloque</div><div class='house-cost'>{money(c2)}</div><div class='delta-down'>▼ {abs(d12):.1f}%</div></div>
    <div class='house-card'><div class='house-icon'>🏘️</div><div class='house-name'>Casa 3 · Superbloque</div><div class='house-cost'>{money(c3)}</div><div class='delta-down'>▼ {abs(d23):.1f}%</div></div>
    <div class='house-card'><div class='house-icon'>🧱</div><div class='house-name'>Casa 4 · Block convencional</div><div class='house-cost'>{money(c4)}</div><div class='delta-flat'>EN PROCESO</div></div>
    </div>""",unsafe_allow_html=True)
    st.warning(f"Casa 4 todavía NO tiene piso, duchas, inodoros, lavatorios, muebles de melamina, zacate, puertas, ventanas ni policarbonato. Por eso {money(c4)} es costo ejecutado, no costo final.")
    view=st.selectbox('Visualización del costo por casa',['Ejecutado + pendiente Casa 4','Trayectoria terminadas','Burbujas comparativas'])
    if view=='Ejecutado + pendiente Casa 4':
        fig=go.Figure()
        fig.add_bar(x=house_order,y=costs.values,name='Ejecutado / terminado')
        fig.add_bar(x=house_order,y=[0,0,0,H4_PENDING_TOTAL],name='Pendiente confirmado/proyectado')
        fig.update_layout(barmode='stack')
    elif view=='Trayectoria terminadas':
        fig=go.Figure(go.Scatter(x=house_order[:3],y=costs.values[:3],mode='lines+markers+text',text=[money(v) for v in costs.values[:3]],textposition='top center',line=dict(width=8,shape='spline'),marker=dict(size=30,symbol='hexagon')))
    else:
        fig=go.Figure(go.Scatter(x=house_order,y=[1]*4,mode='markers+text',text=[money(v) for v in costs.values],textposition='top center',marker=dict(size=np.sqrt(costs.values/max(costs.max(),1))*105+35)));fig.update_yaxes(visible=False)
    fig.update_layout(title='Costo reconstruido · Casa 4 separa ejecutado de pendiente',height=470)
    st.plotly_chart(fig,use_container_width=True)
    chart_explain('Casas 1–3 son viviendas terminadas. Casa 4 muestra únicamente lo ejecutado; en la vista apilada se agrega por separado lo que sabemos que falta.','No comparar el costo ejecutado de Casa 4 directamente contra una vivienda terminada. Usar la proyección solo como escenario de terminación.')
    st.markdown('### 🧩 Qué falta todavía en Casa 4')
    pend_df=pd.DataFrame({'Componente':list(H4_PENDING_DETAIL.keys()),'Costo estimado':list(H4_PENDING_DETAIL.values())}).sort_values('Costo estimado')
    fig=px.bar(pend_df,x='Costo estimado',y='Componente',orientation='h',text_auto='.3s')
    fig.update_layout(height=390,title=f'Pendiente identificado/proyectado · {money(H4_PENDING_TOTAL)}')
    st.plotly_chart(fig,use_container_width=True)
    st.markdown(f"<div class='sourcebox'><b>Proyección mínima con pendientes conocidos:</b> ejecutado {money(H4_EXECUTED)} + pendiente {money(H4_PENDING_TOTAL)} = <b>{money(H4_PROJECTED)}</b>. Esta cifra no se presenta como costo final cerrado: faltan validar otros posibles componentes de terminación.</div>",unsafe_allow_html=True)
    st.markdown("<div class='sourcebox'><b>Lectura histórica:</b> Casa 1, Casa 2 y Casa 3 son Superbloque terminadas. Casa 4 usa block convencional y sigue en proceso. La reducción entre Casas 1–3 sí es comparable; Casa 4 requiere proyectar terminación antes de comparar sistemas.</div>",unsafe_allow_html=True)

with ti['🧱 Receta visual']:
    st.subheader('🧱 Dos recetas distintas')
    st.caption('Las tres primeras casas permiten reconstruir la receta Superbloque. Casa 4 aporta la estructura convencional real; los componentes aún no ejecutados se proyectan desde las casas terminadas.')
    rt=st.radio('Receta',['🏗️ Superbloque · Casas 1–3','🧱 Block convencional · Casa 4'],horizontal=True)
    recx=rec_sb.copy() if rt.startswith('🏗️') else rec_conv.copy()
    if rt.startswith('🧱'):
        st.info('Casa 4: estructura y materiales ejecutados = observados/reconstruidos. Piso, sanitarios, melamina, zacate, puertas/ventanas y policarbonato = pendientes proyectados.')
    rv=st.selectbox('Visualización de la receta',['Treemap de costo','Sunburst por familia','Mapa cantidad × costo'])
    q=recx[recx.Costo_base>0].copy()
    if rv=='Mapa cantidad × costo':
        q['Peso']=np.log1p(q.Cantidad_base.clip(lower=0))*np.log1p(q.Costo_base.clip(lower=0));fig=px.scatter(q,x='Cantidad_base',y='Costo_base',size='Peso',color='Familia',hover_name='Material_homologado',hover_data=['Estado'])
    elif rv.startswith('Sunburst'):fig=px.sunburst(q,path=['Familia','Material_homologado'],values='Costo_base')
    else:fig=px.treemap(q,path=['Familia','Material_homologado'],values='Costo_base')
    fig.update_layout(height=560);st.plotly_chart(fig,use_container_width=True)
    chart_explain('El tamaño representa el costo reconstruido de cada componente dentro de la receta seleccionada.','Usar recetas separadas para cotizar futuras viviendas sin mezclar el costo del sistema Superbloque con la estructura convencional.')
    st.dataframe(recx.sort_values('Costo_base',ascending=False).head(40),use_container_width=True,hide_index=True)
    st.markdown('### 🗓️ Ruta de abastecimiento');scale=st.radio('Escala',['Semanas','Meses'],horizontal=True,index=0)
    for name,a,b,mats in STAGE_PLAN:
        if scale=='Meses':a,b=(a-1)//4+1,(b-1)//4+1
        chips=''.join(f"<span class='chip'>{m}</span>" for m in mats);st.markdown(f"<div class='material-card'><div class='title'>{name}</div><div class='meta'>{'Semana' if scale=='Semanas' else 'Mes'} {a} → {b}</div><div style='margin-top:8px'>{chips}</div></div>",unsafe_allow_html=True)

with ti['🏪 Material × proveedor']:
    st.subheader('🏪 Comparación material × proveedor');st.caption('Solo MIN, MAX y TOTAL GASTADO. Sin promedio ni mediana.')
    valid=scope[scope.Precio_unitario>0].copy();order=(valid.groupby('Material_homologado').agg(Cantidad=('Cantidad','sum'),Relevancia=('Relevancia','min'),Gasto=('Total_linea','sum')).sort_values(['Relevancia','Cantidad','Gasto'],ascending=[True,False,False]).index.tolist());mat=st.selectbox('Material',order);comps=valid.loc[valid.Material_homologado.eq(mat),'Comparable'].value_counts().index.tolist();ck=st.selectbox('Producto/presentación comparable',comps);x=valid[(valid.Material_homologado.eq(mat))&(valid.Comparable.eq(ck))].copy();usekg=x.Precio_por_kg.notna().any();mode=st.radio('Comparar por',['Precio por kg','Precio por presentación'],horizontal=True,index=0) if usekg else 'Precio por presentación';metric='Precio_por_kg' if mode=='Precio por kg' else 'Precio_unitario';x=x[x[metric].notna()];ss=supplier_stats(x,metric).sort_values('Precio_min');vv=st.selectbox('Visualización',['Dumbbell MIN ↔ MAX','Barras: rango y gasto','Heatmap MIN/MAX'])
    if ss.empty:st.info('No hay datos comparables.')
    else:
        if vv.startswith('Dumbbell'):
            fig=go.Figure()
            for _,r in ss.iterrows():fig.add_trace(go.Scatter(x=[r.Precio_min,r.Precio_max],y=[r.Proveedor,r.Proveedor],mode='lines',line=dict(width=9),showlegend=False,hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=ss.Precio_min,y=ss.Proveedor,mode='markers',marker=dict(size=15,symbol='circle'),name='Mínimo'));fig.add_trace(go.Scatter(x=ss.Precio_max,y=ss.Proveedor,mode='markers',marker=dict(size=15,symbol='diamond'),name='Máximo'))
        elif vv.startswith('Barras'):ss['Rango']=ss.Precio_max-ss.Precio_min;fig=px.scatter(ss,x='Precio_min',y='Precio_max',size='Total_gastado',hover_name='Proveedor',hover_data=['Total_gastado','Rango'])
        else:fig=px.imshow(ss.set_index('Proveedor')[['Precio_min','Precio_max']],aspect='auto',text_auto='.0f')
        fig.update_layout(title=f'{mat} · {ck}',height=max(420,120+55*len(ss)));st.plotly_chart(fig,use_container_width=True);chart_explain('Compare el mejor y peor precio pagado por proveedor; el gasto total da contexto al peso del proveedor.','Definir rango de negociación sin depender de promedios.')

with ti['📈 Evolución de precio']:
    st.subheader('📈 Evolución histórica del precio');st.caption('La unidad comercial se valida primero. Clavos EPA se tratan como paquete/bolsa, no como pieza.')
    mats=(scope[scope.Precio_unitario>0].groupby('Material_homologado').Cantidad.sum().sort_values(ascending=False).index.tolist());mat=st.selectbox('Material',mats,key='tm');comps=scope.loc[(scope.Material_homologado.eq(mat))&(scope.Precio_unitario>0),'Comparable'].value_counts().index.tolist();ck=st.selectbox('Producto/presentación comparable',comps,key='tc');x=scope[(scope.Material_homologado.eq(mat))&(scope.Comparable.eq(ck))&(scope.Precio_unitario>0)&scope.Fecha.notna()].copy();usekg=x.Precio_por_kg.notna().any();mode=st.radio('Métrica',['₡ por kg','₡ por presentación'],horizontal=True,index=0) if usekg else '₡ por presentación';metric='Precio_por_kg' if mode=='₡ por kg' else 'Precio_unitario';x=x[x[metric].notna()].sort_values('Fecha');tv=st.selectbox('Visualización',['Línea temporal por proveedor','Small multiples','Rango histórico'])
    if tv=='Small multiples':fig=px.line(x,x='Fecha',y=metric,facet_row='Proveedor',markers=True,height=max(430,220*x.Proveedor.nunique()))
    elif tv.startswith('Rango'):
        rr=x.groupby('Proveedor',as_index=False)[metric].agg(['min','max']).reset_index()
        fig=go.Figure()
        for _,r0 in rr.iterrows():
            fig.add_trace(go.Scatter(x=[r0['min'],r0['max']],y=[r0['Proveedor'],r0['Proveedor']],mode='lines+markers',showlegend=False))
    else:fig=px.line(x,x='Fecha',y=metric,color='Proveedor',markers=True)
    fig.update_layout(title=f'Pulso de precio · {ck}',height=540);st.plotly_chart(fig,use_container_width=True);chart_explain('Cada punto es una compra comparable. La pendiente revela si el precio sube, baja o se mantiene.','Decidir si comprar pronto, negociar o esperar una nueva cotización.')
    ss=supplier_stats(x,metric).sort_values('Ultimo_precio');cols=st.columns(min(3,max(1,len(ss))))
    for i,(_,r) in enumerate(ss.iterrows()):
        icon='📈' if r.Tendencia=='Subiendo' else ('📉' if r.Tendencia=='Bajando' else '➖')
        with cols[i%len(cols)]:st.markdown(f"<div class='rec-card'><div class='rank'>{r.Proveedor}</div><div class='supplier'>{money(r.Ultimo_precio)}</div><div class='signal'>{icon} {r.Tendencia} · {pct(r.Cambio_pct)}</div><div class='meta'>MIN {money(r.Precio_min)} · MAX {money(r.Precio_max)}</div></div>",unsafe_allow_html=True)

if '🚚 Fletes' in ti:
    with ti['🚚 Fletes']:
        st.subheader('🚚 Flete y costo puesto en obra');fh=freight[freight.Casa.isin(['Casa 1','Casa 2','Casa 3','Casa 4'])].copy();st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Flete identificado</div><div class='value'>{money(freight.Total_linea.sum())}</div></div><div class='kpi'><div class='label'>Líneas</div><div class='value'>{len(freight)}</div></div><div class='kpi'><div class='label'>Proveedores</div><div class='value'>{freight.Proveedor.nunique()}</div></div><div class='kpi'><div class='label'>Peso sobre gasto</div><div class='value'>{freight.Total_linea.sum()/scope.Total_linea.sum()*100:.1f}%</div></div></div>",unsafe_allow_html=True);fv=st.selectbox('Visualización',['Sunburst casa → proveedor','Treemap por proveedor','Barras por cargo'])
        if fv.startswith('Sunburst'):fig=px.sunburst(fh,path=['Casa','Proveedor'],values='Total_linea')
        elif fv.startswith('Treemap'):fig=px.treemap(freight,path=['Proveedor','Descripcion_original'],values='Total_linea')
        else:fig=px.bar(freight.sort_values('Total_linea'),x='Total_linea',y='Descripcion_original',orientation='h',color='Proveedor')
        fig.update_layout(height=520);st.plotly_chart(fig,use_container_width=True);chart_explain('El tamaño representa cuánto se pagó en transporte.','Comparar costo puesto en obra y oportunidades de consolidación.')

with ti['🎯 Casas 5 y 6']:
    st.subheader(f'🎯 Centro de planificación · {future_houses}')
    future_system=st.radio('Sistema a planificar',['Superbloque','Block convencional'],horizontal=True)
    st.caption('Cuánto comprar, cuándo, dónde cotizar y qué significa la evolución del precio.')
    rec=(rec_sb if future_system=='Superbloque' else rec_conv).copy()
    rec=rec.rename(columns={'Costo_base':'Costo_hist'})
    rec['Presentacion']='Unidad comercial'
    rec['Relevancia']=3
    rec['Cantidad_meta']=rec.Cantidad_base*(1+waste)*n_future;cand=rec.sort_values(['Relevancia','Costo_hist'],ascending=[True,False]).head(35);rows=[]
    for _,r in cand.iterrows():
        x=scope[(scope.Material_homologado.eq(r.Material_homologado))&(scope.Presentacion.eq(r.Presentacion))&(scope.Precio_unitario>0)].copy()
        if x.empty:continue
        metric='Precio_por_kg' if x.Precio_por_kg.notna().any() else 'Precio_unitario';x=x[x[metric].notna()];ss=supplier_stats(x,metric)
        if ss.empty:continue
        pmin,pmax=ss.Ultimo_precio.min(),ss.Ultimo_precio.max();span=max(pmax-pmin,1);ss['score']=.58*((ss.Ultimo_precio-pmin)/span)+.27*(ss.Cambio_pct.clip(-30,30)/60+.5)-.15*(np.minimum(ss.Compras,5)/5);ss=ss.sort_values('score');f=ss.iloc[0];s=ss.iloc[1] if len(ss)>1 else None;target=ss.Precio_min.min();action,interpret=signal_text(f.Tendencia,f.Ultimo_precio,target);rows.append({**r.to_dict(),'Proveedor_1':f.Proveedor,'Ultimo_1':f.Ultimo_precio,'Tendencia_1':f.Tendencia,'Cambio_1':f.Cambio_pct,'Proveedor_2':s.Proveedor if s is not None else '—','Ultimo_2':s.Ultimo_precio if s is not None else np.nan,'Precio_meta':target,'Metrica':'₡/kg' if metric=='Precio_por_kg' else '₡/presentación','Accion':action,'Interpretacion':interpret})
    plan=pd.DataFrame(rows);build_animation(n_future)
    if plan.empty:st.info('No hay suficientes datos para construir recomendaciones.')
    else:
        risky=(plan.Tendencia_1=='Subiendo').sum();st.markdown(f"<div class='kpi-grid'><div class='kpi'><div class='label'>Materiales priorizados</div><div class='value'>{len(plan)}</div></div><div class='kpi'><div class='label'>Tendencia al alza</div><div class='value'>{risky}</div><div class='sub'>Negociar primero</div></div><div class='kpi'><div class='label'>Margen</div><div class='value'>{waste*100:.0f}%</div></div><div class='kpi'><div class='label'>Casas</div><div class='value'>{n_future}</div></div></div>",unsafe_allow_html=True);material=st.selectbox('Explorar material',plan.Material_homologado.tolist());r=plan[plan.Material_homologado.eq(material)].iloc[0];icon='📈' if r.Tendencia_1=='Subiendo' else ('📉' if r.Tendencia_1=='Bajando' else '➖');c1,c2,c3=st.columns(3)
        with c1:st.markdown(f"<div class='rec-card'><div class='rank'>Cantidad objetivo</div><div class='supplier'>{r.Cantidad_meta:,.1f}</div><div class='meta'>{r.Presentacion} · incluye {waste*100:.0f}% seguridad</div></div>",unsafe_allow_html=True)
        with c2:st.markdown(f"<div class='rec-card'><div class='rank'>🥇 Primera opción</div><div class='supplier'>{r.Proveedor_1}</div><div class='signal'>{icon} {r.Tendencia_1} · {pct(r.Cambio_1)}</div><div class='meta'>Último {money(r.Ultimo_1)} · {r.Metrica}</div></div>",unsafe_allow_html=True)
        with c3:st.markdown(f"<div class='rec-card'><div class='rank'>🎯 Meta</div><div class='supplier'>{money(r.Precio_meta)}</div><div class='meta'>{r.Metrica} · mínimo comparable</div></div>",unsafe_allow_html=True)
        st.markdown(f"<div class='explain'><b>{r.Accion}</b><br>{r.Interpretacion}<br><b>Alternativa:</b> {r.Proveedor_2} · último {money(r.Ultimo_2)}.</div>",unsafe_allow_html=True);pv=st.selectbox('Visualización del plan',['Prioridad de negociación','Sankey material → proveedor','Ranking de urgencia'])
        if pv=='Prioridad de negociación':
            q=plan.copy();q['Brecha']=q.Ultimo_1-q.Precio_meta
            fig=px.bar(q.sort_values('Brecha').tail(20),x='Brecha',y='Material_homologado',orientation='h',hover_data=['Proveedor_1','Presentacion','Metrica'])
        elif pv.startswith('Sankey'):
            q=plan.head(18);mats=q.Material_homologado.tolist();provs=list(dict.fromkeys(q.Proveedor_1.tolist()));labs=mats+provs;src=[];tgt=[];val=[]
            for _,z in q.iterrows():src.append(labs.index(z.Material_homologado));tgt.append(labs.index(z.Proveedor_1));val.append(max(float(z.Costo_hist),1))
            fig=go.Figure(go.Sankey(node=dict(label=labs,pad=12,thickness=16),link=dict(source=src,target=tgt,value=val)))
        else:
            q=plan.copy();q['Urgencia']=np.where(q.Tendencia_1.eq('Subiendo'),3,np.where(q.Tendencia_1.eq('Estable'),2,1))
            fig=px.bar(q.sort_values(['Urgencia','Costo_hist']).tail(20),x='Urgencia',y='Material_homologado',orientation='h',hover_data=['Proveedor_1','Precio_meta','Cantidad_meta'])
        fig.update_layout(height=560,title='Plan de compra priorizado');st.plotly_chart(fig,use_container_width=True);chart_explain('Tamaño = impacto económico; tendencia, brecha y volumen indican riesgo u oportunidad.','Ordenar cotizaciones y negociaciones por prioridad real.');st.download_button('⬇️ Descargar plan',plan.to_csv(index=False).encode('utf-8-sig'),'plan_compras_casas_5_6.csv','text/csv')

with ti['🔎 Explorador maestro']:
    st.subheader('🔎 Explorador maestro');st.caption('La base original se conserva íntegra. La asignación reconstruida por casa está incluida en asignacion_auditada_4_casas.csv dentro del paquete.');c1,c2,c3,c4=st.columns(4);c1.metric('Líneas',f'{len(df):,}');c2.metric('Materiales',df.Material_homologado.nunique());c3.metric('Proveedores',df.Proveedor.nunique());c4.metric('Pendientes manuales','0');search=st.text_input('🔍 Buscar');a,b,c=st.columns(3)
    with a:fam=st.multiselect('Familia',sorted(df.Familia.dropna().unique()))
    with b:prov=st.multiselect('Proveedor',sorted(df.Proveedor.dropna().unique()))
    with c:typ=st.multiselect('Tipo',sorted(df.Tipo_registro.dropna().unique()))
    z=df.copy()
    if fam:z=z[z.Familia.isin(fam)]
    if prov:z=z[z.Proveedor.isin(prov)]
    if typ:z=z[z.Tipo_registro.isin(typ)]
    if search:q=re.escape(search);z=z[z.Material_homologado.str.contains(q,case=False,regex=True,na=False)|z.Descripcion_original.str.contains(q,case=False,regex=True,na=False)|z.Proveedor.str.contains(q,case=False,regex=True,na=False)|z.Factura.astype(str).str.contains(q,case=False,regex=True,na=False)]
    st.markdown(f"<div class='explain'><b>{len(z):,}</b> registros. La columna <b>Unidad comercial</b> evita mezclar paquetes con piezas.</div>",unsafe_allow_html=True);cols=['Fecha','Proveedor','Factura','Material_homologado','Descripcion_original','Cantidad','Presentacion','Unidad_comercial','Comparable','Precio_unitario','Precio_por_kg','Total_linea','Familia','Tipo_registro','Confianza_homologacion'];st.dataframe(z[cols].sort_values('Fecha',ascending=False),use_container_width=True,hide_index=True,height=530);st.download_button('⬇️ Descargar selección',z.to_csv(index=False).encode('utf-8-sig'),'base_maestra_filtrada_v5.csv','text/csv')
st.divider();st.caption('Construir Mejor · formato V5 · análisis auditado · 3 casas Superbloque terminadas + Casa 4 convencional en proceso · dos recetas · Casas 5 y 6.')
