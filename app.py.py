import streamlit as st
import pandas as pd
from datetime import datetime
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io

# Configuración de página de la App Web
st.set_page_config(page_title="Fábrica de Gantt - Marketing", layout="wide")

# ==========================================
# DEFINE LAS IDENTIDADES DE MARCA
# ==========================================
ESTILOS_MARCAS = {
    "FULL_SPORT": {
        "bg_primary": "#000000", "accent_primary": "#FF00FF", "accent_secondary": "#00E5FF",
        "text_main": "#FFFFFF", "text_dim": "#8E8E93", "border_color": "#2C2C2E"
    },
    "VILLAVICENCIO": {
        "bg_primary": "#FFFFFF", "accent_primary": "#00A3E0", "accent_secondary": "#E4002B",
        "text_main": "#1C1C1E", "text_dim": "#636366", "border_color": "#E5E5EA"
    },
    "VDS": {
        "bg_primary": "#0A192F", "accent_primary": "#00B4D8", "accent_secondary": "#FF8A7A",
        "text_main": "#F8F9FA", "text_dim": "#94A3B8", "border_color": "#1E293B"
    },
    "LEVITE": {
        "bg_primary": "#F4F9F4", "accent_primary": "#005A9C", "accent_secondary": "#A3E4D7",
        "text_main": "#1E3A1E", "text_dim": "#7A9A7A", "border_color": "#E0EBE0"
    }
}

st.title("🛠️ La Fábrica de Gantt de Marketing")
st.markdown("Pegá tu tabla de Excel, elegí tu marca y bajá tu slide en PNG de forma automática.")

# ==========================================
# PANEL LATERAL - CONFIGURACIÓN DE MARCA
# ==========================================
with st.sidebar:
    st.header("🎨 Personalización")
    marca = st.selectbox("Elegí la Marca:", list(ESTILOS_MARCAS.keys()))
    config = ESTILOS_MARCAS[marca]
    
    proyecto_tag = st.text_input("Subtítulo de la slide:", "CRONOGRAMA DE OPERACIONES 2026")
    titulo_slide = st.text_input("Título principal:", "Lanzamiento Estratégico de Campaña")

# ==========================================
# PANEL PRINCIPAL - CARGA DE DATOS
# ==========================================
st.subheader("📋 Paso 1: Pegá tus celdas de Excel abajo")
data_input = st.text_area("Pegá acá tus datos de Excel directamente:", height=180)

if data_input:
    try:
        lines = [line.strip() for line in data_input.strip().split('\n') if line.strip()]
        
        tareas_lista = []
        hitos_lista = []
        fecha_pattern = r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        
        for line in lines:
            fechas_encontradas = re.findall(fecha_pattern, line)
            if not fechas_encontradas:
                continue
            
            partes = re.split(r'\t|\s{2,}', line)
            name = partes[0] if partes else "Tarea Sin Nombre"
            tipo = "hito" if "hito" in line.lower() else "barra"
            
            if tipo == "hito":
                fec = datetime.strptime(fechas_encontradas[0], "%d/%m/%Y")
                hitos_lista.append({"name": name, "date": fec})
            else:
                if len(fechas_encontradas) >= 2:
                    ini = datetime.strptime(fechas_encontradas[0], "%d/%m/%Y")
                    fin = datetime.strptime(fechas_encontradas[1], "%d/%m/%Y")
                    tareas_lista.append({"name": name, "start": ini, "end": fin})

        # --- ORDENAR ESCALONADO POR FECHA DE INICIO ---
        # Se invierte para que la que empieza antes quede arriba de todo en el gráfico de Matplotlib
        tareas_lista = sorted(tareas_lista, key=lambda x: x["start"], reverse=True)

        if not tareas_lista and not hitos_lista:
            st.warning("No se encontraron datos válidos.")
            st.stop()

        # ==========================================
        # MOTOR DE DIBUJO DE IMAGEN (Matplotlib 16:9)
        # ==========================================
        fig, ax = plt.subplots(figsize=(13.333, 7.5), dpi=150)
        fig.patch.set_facecolor(config["bg_primary"])
        ax.set_facecolor(config["bg_primary"])

        # Dibujar Barras
        for i, t in enumerate(tareas_lista):
            color_bar = config["accent_primary"] if i % 2 == 0 else config["accent_secondary"]
            duracion = (t["end"] - t["start"]).days
            if duracion <= 0: duracion = 1
            
            # Dibujar la barra de la tarea
            ax.barh(i, duracion, left=t["start"], height=0.4, 
                    color=color_bar, edgecolor='none', alpha=0.9, zorder=3)
            
            # Etiqueta de la tarea arriba de la barra
            ax.text(t["start"], i + 0.28, t["name"].upper(), color=config["text_main"], 
                    fontsize=9, fontweight='bold', va='bottom', ha='left')
            
            # Fechas al final de la barra
            fechas_str = f"{t['start'].strftime('%d/%m')} a {t['end'].strftime('%d/%m')}"
            ax.text(t["end"] + pd.Timedelta(days=2), i, fechas_str, color=config["text_dim"], 
                    fontsize=8, va='center', ha='left', style='italic')

        # Dibujar Hitos
        for h in hitos_lista:
            ax.axvline(x=h["date"], color=config["accent_secondary"], linestyle="--", linewidth=1.2, zorder=2)
            ax.text(h["date"], len(tareas_lista) - 0.5, f" 📍 {h['name'].upper()}\n ({h['date'].strftime('%d/%m')})", 
                    color=config["accent_secondary"], fontsize=8, fontweight='bold', va='bottom', ha='center')

        # Formatear la línea de tiempo de los meses
        ax.set_yticks([])
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%B \'%y'))
        
        ax.tick_params(axis='x', colors=config["text_dim"], labelsize=10, pad=10)
        ax.xaxis.tick_top()
        
        for spine in ["left", "right", "bottom", "top"]:
            ax.spines[spine].set_visible(False)
            
        ax.spines["top"].set_color(config["border_color"])
        ax.spines["top"].set_visible(True)
        ax.spines["top"].set_linewidth(1.5)

        # Inyectar textos corporativos principales
        plt.text(0.04, 0.94, proyecto_tag.upper(), transform=fig.transFigure, color=config["accent_primary"], fontsize=11, fontweight='bold')
        plt.text(0.04, 0.88, titulo_slide.upper(), transform=fig.transFigure, color=config["text_main"], fontsize=22, fontweight='bold')
        
        # Footer
        plt.text(0.04, 0.04, f"{marca.replace('_', ' ')} / CREATIVE & OPERATIONS", transform=fig.transFigure, color=config["text_main"], fontsize=9, fontweight='bold')
        plt.text(0.96, 0.04, "DIAPOSITIVA AUTOMATIZADA", transform=fig.transFigure, color=config["text_dim"], fontsize=9, ha='right')

        plt.tight_layout()
        plt.subplots_adjust(top=0.76, bottom=0.12, left=0.05, right=0.88)

        # Generar buffer para descarga
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
        img_buffer.seek(0)
        plt.close()

        # Mostrar la vista previa
        st.subheader("🖼️ Paso 2: Tu Diapositiva está lista")
        st.image(img_buffer, use_column_width=True)

        # Botón nativo de descarga
        st.download_button(
            label="📥 Descargar Diapositiva en PNG",
            data=img_buffer,
            file_name=f"Gantt_{marca}_{datetime.now().strftime('%Y%m%d')}.png",
            mime="image/png"
        )

    except Exception as e:
        st.error(f"Error al procesar el Excel. Detalles: {e}")