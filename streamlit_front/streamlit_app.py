import os

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

st.set_page_config(layout='wide')


def return_genre() -> str:
    genre = st.radio(
        "Выберите оцениваемый параметр:",
        ["Обслуживание", "Цена", "Ассортимент", "Качество", "Чистота", "Расположение"],
    )

    agg_idx = ''
    if genre == "Обслуживание":
        agg_idx = 'service'
    elif genre == "Цена":
        agg_idx = 'prices'
    elif genre == "Ассортимент":
        agg_idx = 'assortment'
    elif genre == "Качество":
        agg_idx = 'quality'
    elif genre == "Чистота":
        agg_idx = 'cleanliness'
    else:
        agg_idx = 'location'
    return agg_idx


def get_color_line(df: pd.DataFrame) -> pd.DataFrame:
    x5_stores = ['Пятерочка']
    df['line_color'] = 1
    df['line_color'] = df['line_color'].astype(object)
    for i in df.index:
        df.loc[df.index == i, 'store_name'] = df.loc[df.index == i, 'store_name'].item().split()[0]
        if df.loc[df.index == i, 'store_name'].item() in x5_stores:
            df.iat[i, -1] = [0, 0, 139]
        else:
            df.iat[i, -1] = [128, 0, 0]
    return df


def get_color_scatter(df: pd.DataFrame, agg_idx: str) -> pd.DataFrame:
    df['scatter_color'] = 1
    df['scatter_color'] = df['scatter_color'].astype(object)
    for i in df.index:
        param = df.loc[df.index == i, agg_idx].item()
        if param > 0:
            df.iat[i, -1] = [34, 139, 34]
        elif param < 0:
            df.iat[i, -1] = [255, 0, 0]
        else:
             df.iat[i, -1] = [128, 128, 128]
    return df


def agg_by_col(df: pd.DataFrame, agg_idx: str) -> pd.DataFrame:
    df = df.drop(columns=['store_type', 'store_district', 'text', 'date', ])
    df = df.groupby(by=['store_address'], as_index=False).agg(agg_col=(agg_idx, 'sum'),
                                                              lat=('lat', 'first'),
                                                              lon=('lon', 'first'),
                                                              store_name=('store_name', 'first'))
    df.rename(columns={'agg_col': agg_idx}, inplace=True)
    return df


def build_map(df: pd.DataFrame) -> None:
    layer = pdk.Layer(
        "ScatterplotLayer",
        df[['lat', 'lon', 'store_address', 'line_color', 'store_name', 'scatter_color']],
        get_position='[lon, lat]',
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=15,
        radius_max_pixels=17,
        line_width_min_pixels=1,
        get_radius="exits_radius",
        get_fill_color='scatter_color',
        get_line_color='line_color',
    )

    view_state = pdk.ViewState(
        latitude=df['lat'].median(),
        longitude=df['lon'].median(),
        zoom=10,
        min_zoom=11,
        max_zoom=18,
        pitch=0,
        bearing=0,
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='light',
        tooltip={
            'text': '{store_name}\n{store_address}',
            'style': {'backgroundColor': 'stelblue', 'color': 'dark'},
        },
    )

    st.subheader('Map')
    st.pydeck_chart(r, use_container_width=True)


if __name__ == "__main__":
    reviews_file = os.path.join(os.getcwd(), 'data', 'reviews_all_yandex_final_pipeline.csv')
    coord_file = os.path.join(os.getcwd(), 'data', 'coord-all-yandex.xlsx')
    df = pd.read_csv(reviews_file)
    coord = pd.read_excel(coord_file)
    df = df.merge(coord, how='left')
    df = df.rename(columns={'store_latitude': 'lat', 'store_longitude': 'lon'})

    agg_idx = return_genre()

    df = agg_by_col(df, agg_idx)
    df = get_color_line(df)
    df = get_color_scatter(df, agg_idx)

    build_map(df)
