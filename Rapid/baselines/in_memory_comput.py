import pandas as pd
import time
from udf.inmemory_udf import polygon_area, polygon_perimeter, polygon_center, grid_index_cal, grid_geometry_gen


start_time = time.time()

df = pd.read_csv('./CA_polygon.csv')
df['coord'].astype(str)

# Features calculation
df['area'] = df['coord'].apply(polygon_area)
df['perimeter'] = df['coord'].apply(polygon_perimeter)
df['lon'] = df['coord'].apply(lambda row: polygon_center(col=row, cor='lon'))
df['lat'] = df['coord'].apply(lambda row: polygon_center(col=row, cor='lat'))

# PIG calculation
df['grid_id'] = df.apply(lambda row: grid_index_cal(x=row['lon'], y=row['lat'], x_min=-180, x_max=180, y_min=-90, y_max=90, res=0.1), axis=1)

# Aggregation
df_agg = pd.DataFrame()
df_agg['grid_id'] = df.groupby('grid_id').groups.keys()
df_agg['count'] = df.groupby('grid_id')['id'].count()
df_agg['area'] = df.groupby('grid_id')['area'].sum()
df_agg['perimeter'] = df.groupby('grid_id')['perimeter'].sum()
df_agg['geometry'] = df_agg['grid_id'].apply(lambda row: grid_geometry_gen(row, -180, 180, -90, 90, -.1))

end_time = time.time()

print(end_time - start_time)

