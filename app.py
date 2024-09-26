import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from openpyxl.styles import Alignment

# Función para calcular la amortización y generar el resumen
def calcular_amortizacion(valor_uef, valor_propiedad_uef, tasa_interes_anual, anios_prestamo, porcentaje_pie, bono_pie):
    # Convertir la tasa de interés anual a mensual
    tasa_interes_mensual = (tasa_interes_anual / 100) / 12

    # Convertir el valor de la propiedad de UEF a CLP
    valor_propiedad_clp = valor_propiedad_uef * valor_uef

    # Calcular el nuevo valor de la propiedad con el bono pie
    valor_propiedad_clp_con_bono = valor_propiedad_clp * (1 + bono_pie)

    # Calcular el pie y el monto del préstamo
    pie = valor_propiedad_clp_con_bono * porcentaje_pie  # Ajuste aquí
    monto_prestamo = valor_propiedad_clp_con_bono * (1 - porcentaje_pie)

    # Número total de meses
    total_meses = anios_prestamo * 12

    # Calcular la cuota mensual con la fórmula de pago de hipoteca
    cuota_mensual = monto_prestamo * (tasa_interes_mensual * (1 + tasa_interes_mensual) ** total_meses) / ((1 + tasa_interes_mensual) ** total_meses - 1)

    # Crear la tabla de amortización
    columnas = ['Mes', 'Pago Mensual', 'Intereses Pagados', 'Capital Pagado', 'Saldo Capital']
    tabla_amortizacion = []

    saldo_restante = monto_prestamo

    for mes in range(1, total_meses + 1):
        intereses_mes = saldo_restante * tasa_interes_mensual
        capital_mes = cuota_mensual - intereses_mes
        saldo_restante -= capital_mes
        tabla_amortizacion.append([mes, cuota_mensual, intereses_mes, capital_mes, saldo_restante])

    # Convertir la tabla de amortización a un DataFrame de pandas
    df_amortizacion = pd.DataFrame(tabla_amortizacion, columns=columnas)

    # Calcular el total pagado y el total de intereses
    total_pagado = df_amortizacion['Pago Mensual'].sum()
    total_intereses = df_amortizacion['Intereses Pagados'].sum()

    # Crear un resumen del préstamo
    resumen_prestamo = {
        'Valor de la propiedad inicial (UF)': valor_propiedad_uef,
        'Valor de la propiedad inicial (CLP)': valor_propiedad_clp,
        'Valor de la propiedad con bono pie (CLP)': valor_propiedad_clp_con_bono,
        'Monto del préstamo (CLP)': monto_prestamo,
        'Pie (CLP)': pie,
        'Tasa de interés anual (%)': tasa_interes_anual,
        'Cuota mensual (CLP)': cuota_mensual,
        'Total pagado (CLP)': total_pagado,
        'Total intereses pagados (CLP)': total_intereses,
        'Duración del préstamo (meses)': total_meses
    }

    # Convertir el resumen a un DataFrame
    df_resumen = pd.DataFrame(list(resumen_prestamo.items()), columns=['Descripción', 'Valor'])

    return df_amortizacion, df_resumen

# Función para generar el archivo Excel
def generar_excel(df_amortizacion, df_resumen):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        df_amortizacion.to_excel(writer, sheet_name='Amortización', index=False)

        # Ajustar el formato de las hojas de Excel
        workbook = writer.book
        for sheet_name in ['Resumen', 'Amortización']:
            worksheet = workbook[sheet_name]
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter  # Get the column name
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column].width = adjusted_width

            # Formatear los números con puntos como separadores de miles
            for row in worksheet.iter_rows(min_row=2, min_col=2):
                for cell in row:
                    if isinstance(cell.value, (int, float)):
                        cell.number_format = '#,##0'

            # Alinear el texto al centro
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

    output.seek(0)
    return output

# Configuración de la aplicación Streamlit
st.title("Análisis Hipotecario")
st.write("""
Esta aplicación permite calcular la amortización de un préstamo hipotecario y generar un resumen detallado.
Puedes ajustar los parámetros y ver los resultados en tiempo real.
""")

# Mostrar la imagen centrada
st.image("img/inmobiliario.jpg", width=350)

# Parámetros de entrada en 3 columnas y 2 filas
col1, col2, col3 = st.columns(3)

with col1:
    valor_uef = st.number_input("Valor de la UEF (CLP)", value=37895.28)
    tasa_interes_anual = st.number_input("Tasa de interés anual (%)", value=4.5)
    porcentaje_pie = st.number_input("Porcentaje de pie (%)", value=10) / 100

with col2:
    valor_propiedad_uef = st.number_input("Valor de la propiedad (UF)", value=3500)
    anios_prestamo = st.selectbox("Años del préstamo", options=[20, 25, 30])
    bono_pie = st.number_input("Bono de pie (%)", value=10) / 100

# Botón para calcular
if st.button("Calcular"):
    # Calcular la amortización y el resumen
    df_amortizacion, df_resumen = calcular_amortizacion(valor_uef, valor_propiedad_uef, tasa_interes_anual, anios_prestamo, porcentaje_pie, bono_pie)

    # Mostrar el texto narrativo
    texto_narrativo = f"""
    Resumen del Análisis Hipotecario:

    - Valor de la propiedad inicial: {valor_propiedad_uef} UF ({df_resumen.loc[1, 'Valor']:,.0f} CLP)
    - Valor de la propiedad con bono pie: {df_resumen.loc[2, 'Valor']:,.0f} CLP
    - Pie inicial: {df_resumen.loc[4, 'Valor']:,.0f} CLP
    - Monto del préstamo: {df_resumen.loc[3, 'Valor']:,.0f} CLP
    - Tasa de interés anual: {df_resumen.loc[5, 'Valor']:.1f}%
    - Cuota mensual: {df_resumen.loc[6, 'Valor']:,.0f} CLP
    - Total pagado al final del préstamo: {df_resumen.loc[7, 'Valor']:,.0f} CLP
    - Total de intereses pagados: {df_resumen.loc[8, 'Valor']:,.0f} CLP
    - Duración del préstamo: {df_resumen.loc[9, 'Valor']} meses ({anios_prestamo} años)

    Este análisis considera un bono de pie del {bono_pie*100:.0f}%, lo que ajusta el valor de la propiedad y el monto del préstamo en consecuencia.
    """
    st.write(texto_narrativo)

    # Mostrar las primeras 5 filas de cada tabla
    st.write("### Primeras 5 filas de la tabla de amortización")
    st.write(df_amortizacion.head())

    st.write("### Primeras 5 filas del resumen del préstamo")
    st.write(df_resumen.head())

    # Botón para descargar el archivo Excel
    output = generar_excel(df_amortizacion, df_resumen)
    st.download_button(
        label="Descargar resumen en Excel",
        data=output,
        file_name="resumen_hipotecario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Crear el gráfico dinámico
    st.write("### Gráfico de distribución de pagos entre intereses y capital")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_amortizacion['Mes'], df_amortizacion['Intereses Pagados'], label='Intereses Pagados')
    ax.plot(df_amortizacion['Mes'], df_amortizacion['Capital Pagado'], label='Capital Pagado')
    ax.set_xlabel('Mes')
    ax.set_ylabel('Monto (CLP)')
    ax.set_title('Distribución de Pagos entre Intereses y Capital')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
