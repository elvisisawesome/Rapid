
## Rasterizing global building footprints in 0.1^{circ} resolution

##### 1. Connect the ECS server
1. open the ssh tool
2. ssh the server: 
```
ssh vldb_test@221.228.10.210
password: 123456
```
##### 2. Run the rasterization example
1. Use the following command to run the example: 
```
conda activate vldb_test
python rapid_example.py
```
##### 3. Used SQL queries in this example

```
CREATE TABLE global_polygon_features_vldb AS

SELECT

polygon_area_udf(geometry) AS area,

polygon_perimeter_udf(geometry) AS perimeter,

polygon_center_udf(geometry, "lon") AS lon,

polygon_center_udf(geometry, "lat") AS lat

FROM global_polygon_0102;
```
```
CREATE TABLE global_polygon_index_res01_vldb AS

SELECT

area,

perimeter,

grid_index_cal(lon, lat, -180, 180, -90, 90, 0.1) AS grid_id

FROM global_polygon_features_vldb;

```
```
CREATE TABLE global_result_res01_vldb AS

SELECT

grid_id,

count(*) AS count,

sum(area) AS area,

sum(perimeter) AS perimeter,

grid_geometry_gen(grid_id, -180, 180, -90, 90, 0.1) AS geometry

FROM global_polygon_index_res01_vldb

GROUP BY grid_id;
```
