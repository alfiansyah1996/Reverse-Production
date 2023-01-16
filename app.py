import streamlit as st
import pandas as pd
import numpy as np
import base64 
from io import StringIO, BytesIO  




st.set_page_config(page_title='Reverse Production')
st.title('Reverse Production App')


def generate_excel_download_link(df):
    # Credit Excel: https://discuss.streamlit.io/t/how-to-add-a-download-excel-csv-function-to-a-button/4474/5
    towrite = BytesIO()
    df.to_excel(towrite, encoding="utf-8", index=False, header=True)  # write to BytesIO buffer
    towrite.seek(0)  # reset pointer
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="data_download.xlsx">Download Excel File</a>'
    return st.markdown(href, unsafe_allow_html=True)

st.write("1.Download Current Stock [link](https://pisang.sayurbox.tech/question/2404-inventory-summary-warehouse-area-inventory-management-system?warehouse=Sentul&inventory_system_category=Fruits&inventory_system_category=Vegetables), lalu upload langsung hasil download ke box dibawah")
read_stock = st.file_uploader('Upload Current Stock', type='xlsx')
if read_stock:
	st.markdown('Upload Success')

st.write("2.Download Current Forecast [link](https://drive.google.com/drive/u/0/folders/1j2IM50MA4RaXnsY-cwcvGiwUmwELTFoQ), lalu upload langsung hasil download ke box dibawah")
read_forecast = st.file_uploader('Upload Forecast', type='xlsx')
if read_forecast:
	st.markdown('Upload Success')

st.write("3.Download SKU Variant [link](https://pisang.sayurbox.tech/question/5853-sku-master?warehouse=Sentul&inventory_system_category=Fruits&inventory_system_category=Vegetables), lalu upload langsung hasil download ke box dibawah")
read_sku = st.file_uploader('Upload SKU Variant', type='xlsx')
if read_sku:
	st.markdown('Upload Success')

st.write("4.Input Jumlah SKU yang ingin direverse")
number = st.number_input('Input')
number = int(number)

options = st.multiselect(
    'Pilih Inventory System Category',
    ['Fruits', 'Vegetables'])


process = st.button("Process")
if process:
	stock = pd.read_excel(read_stock)
	stock = stock.loc[(stock['inventory_system_category'] == 'Fruits') | (stock['inventory_system_category'] == 'Vegetables')]
	stock = stock.loc[(stock['Finished_Goods_Storage'] > 0)]
	stock = stock[['warehouse','sku_number','sku_description','inventory_system_category','Finished_Goods_Storage']]
	stock['sku_description_extract'] = stock['sku_description'].str.replace(r'\s*\w+(?:\W+\w+)?\s*(?![^,])', '')
	stock = stock.replace({'sku_description_extract': 'Impor Impor'}, 
                        {'sku_description_extract': 'Impor'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Import'}, 
                        {'sku_description_extract': 'Impor'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Organik Organik'}, 
                        {'sku_description_extract': 'Organik'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Imperfect Imperfect'}, 
                        {'sku_description_extract': 'Imperfect'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Konvensional Konvensional'}, 
                        {'sku_description_extract': 'Konvensional'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Conventional'}, 
                        {'sku_description_extract': 'Konvensional'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Premium Premium'}, 
                        {'sku_description_extract': 'Premium'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Hidroponik Hidroponik'}, 
                        {'sku_description_extract': 'Hidroponik'}, regex=True)
	stock = stock.replace({'sku_description_extract': 'Dummy'}, 
                        {'sku_description_extract': 'Konvensional'}, regex=True)
	stock = stock.replace({'sku_description_extract': ' B2B'}, 
                        {'sku_description_extract': ''}, regex=True)
	stock = stock.replace({'sku_description_extract': ' Konvensional'}, 
                        {'sku_description_extract': ''}, regex=True)
	stock = stock.replace({'sku_description_extract': '  '}, 
                        {'sku_description_extract': ' '}, regex=True)
	sku_base = pd.read_excel(read_sku)

	sku = sku_base[['sku_code','converter','uom_qty','uom_unit']]
	sku.columns = ['sku_number','converter','uom_qty','uom_unit']

	join = pd.merge(
	            left=stock,
	            right=sku,
	            left_on='sku_number',
	            right_on='sku_number',
	            how='left')

	join['converter']=join['uom_qty']
	join.loc[(join['uom_unit'] =='gram'), 'converter'] = join['uom_qty']/1000
	join.loc[(join['uom_unit'] =='gram'), 'uom_unit'] = 'kg'

	join['helper_1']=join['sku_description_extract']+' '+join['uom_unit']

	ids = join["helper_1"]
	join_2 = join[ids.isin(ids[ids.duplicated()])].sort_values("helper_1")

	join_2 = join_2.loc[~(join_2['uom_unit'] == 'pack')]


	total_stock = join_2[['helper_1','Finished_Goods_Storage']]

	total_stock = pd.DataFrame(total_stock.groupby(['helper_1'], as_index = False).sum())

	total_stock.columns = ['helper_1','total_all_stock_in_fg']

	join_3 = pd.merge(
	            left=join_2,
	            right=total_stock,
	            left_on='helper_1',
	            right_on='helper_1',
	            how='left')

	join_3['ratio_stock_in_fg']=join_3['Finished_Goods_Storage']/join_3['total_all_stock_in_fg']






	forecast = pd.read_excel(read_forecast)

	forecast = forecast[['sku_number','forecast']]

	forecast = forecast.dropna()
	forecast = pd.DataFrame(forecast.groupby(['sku_number'], as_index = False).sum())

	forecast.columns =['sku_number','total_forecast_weekly']

	join_4 = pd.merge(
	            left=join_3,
	            right=forecast,
	            left_on='sku_number',
	            right_on='sku_number',
	            how='left')
	join_4['total_forecast_weekly_uos']=join_4['total_forecast_weekly']*join_4['converter']

	total_forecast = join_4[['helper_1','total_forecast_weekly_uos']]

	total_forecast = pd.DataFrame(total_forecast.groupby(['helper_1'], as_index = False).sum())

	total_forecast.columns = ['helper_1','total_forecast_for_fg_uos']

	join_5 = pd.merge(
	            left=join_4,
	            right=total_forecast,
	            left_on='helper_1',
	            right_on='helper_1',
	            how='left')

	join_5 = join_5.fillna(0)

	join_5['ratio_forecast_for_fg']=join_5['total_forecast_weekly_uos']/join_5['total_forecast_for_fg_uos']

	join_5['target_stock_for_fg']=(join_5['ratio_forecast_for_fg']*join_5['total_all_stock_in_fg']).round(0)

	join_5['gap_stock_fg_to_target']=join_5['target_stock_for_fg']-join_5['Finished_Goods_Storage']

	join_5 = join_5[['warehouse','sku_number','sku_description','inventory_system_category','Finished_Goods_Storage',
                'total_forecast_weekly','converter','total_forecast_weekly_uos','ratio_stock_in_fg','ratio_forecast_for_fg','target_stock_for_fg',
		'gap_stock_fg_to_target','uom_unit','sku_description_extract']]

	join_5 = join_5.sort_values(by='gap_stock_fg_to_target', ascending=False)
	join_5

	top10 = join_5.head(number)
	top10

	top10 = top10[['sku_description_extract']]
	top10['top_10']=1

	join_5 = pd.merge(
	            left=join_5,
	            right=top10,
	            left_on='sku_description_extract',
	            right_on='sku_description_extract',
	            how='left')

	join_5 = join_5.loc[(join_5['top_10'] == 1)]

	join_5 = join_5[['warehouse','sku_number','sku_description','inventory_system_category','Finished_Goods_Storage',
                'total_forecast_weekly','converter','total_forecast_weekly_uos','ratio_stock_in_fg','ratio_forecast_for_fg','target_stock_for_fg',
		'gap_stock_fg_to_target','uom_unit']]

	join_5.loc[(join_5['gap_stock_fg_to_target'] > 0), 'note'] = 'production perlu produksi'
	join_5.loc[(join_5['gap_stock_fg_to_target'] < 0), 'note'] = 'inventory perlu move dari fg ke production'
	st.markdown('Process Complated')
	st.dataframe(join_5)

	st.subheader('Downloads:')
	generate_excel_download_link(join_5)
