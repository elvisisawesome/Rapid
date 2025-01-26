'''
created by Yicheng Fu, 17:30 29/11/2024
'''

import sys
from odps.udf import annotate




"""
--------- Common UDF for both polygon and grid ----------
"""

##### Convert EPSG4326 (degree) -> EPSG3857 (meter) or EPSG3857 (meter) -> EPSG4326 (degree) #####
#### Input: 
# epsg: the original epsg of the input coordinate, int (4326 or 3857)
# x: the input coordinate, double
# cor: the longtitude or latitude that x stands for, string (lon or lat)
#### Output: 
# the converted coordinate, double
@annotate("int,double,string->double")
class epsg_convert(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, epsg, x, cor):
        import re
        import math

        def epsg3857_2_4326(x, cor):
            R = 6371008.8  # radius of the earth
            if cor == "lon":
                return (x / R) * (180 / math.pi)  # lon
            elif cor == "lat":
                return math.degrees(math.atan(math.sinh(x / R)))  # lat
            else:
                return -1

        def epsg4326_2_3857(x, cor):
            R = 6371008.8  # radius of the earth
            if cor == "lon":
                return R * math.radians(x) # lon, X
            elif cor == "lat":
                return R * math.log(math.tan(math.pi / 4 + math.radians(x) / 2)) # lat, Y
            else:
                return -1
        
        if epsg == 3857:
            return epsg3857_2_4326(x, cor)
        elif epsg == 4326:
            return epsg4326_2_3857(x, cor)
        else:
            print('Invalid value on EPSG!')
            return -1

##### Rough process of the raw geometry data #####
#### Input:
# geometry: the raw geometry read from the csv, string
#### Output:
# geometry_p: processed geometry, string
@annotate("string->string")
@annotate("int,double,string->double")
class geometry_process(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, geometry):
        import re
        import math
        geometry_dict = eval(geometry)
        return str(geometry_dict['coordinates'])



"""
-------- Calculate the area, perimeter, center, grid_index for polygon ---------
def Mypolygon_Area:
def Mypolygon_Perimeter:
def Mypolygon_Center:
"""



@annotate("string->double")
class Mypolygon_Area(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self,col):
        import re
        from math import radians, cos, sin, sqrt
        col = col[3:-3]
        #col = re.split(r'\],\s*\[|,', col)
        col = re.split(r'[,\[\]\s]+', col)
        col = [item for item in col if item]  
        len_ls = len(col)
        # assert len_ls % 2 == 0,'warning info_ls is not even'
        if len_ls % 2 != 0:
            col = [x for x in col if x != '0.0']
            len_ls = len(col)
        if len_ls < 2:
            return 0
        #x = radians(coords[0]) * cos(radians(coords[1]))
        #y = radians(coords[1])
        col = [(radians((float(col[i])) * cos(radians(float(col[i+1])))), radians(float(col[i+1]))) for i in range(0,len_ls,2)]
        total_area = 0
        for i,vertex in enumerate(col[1:-1],start=1):
            f = lambda point_a, point_b, point_c:  0.5*((point_b[0] - point_a[0])*(point_c[1] - point_a[1]) -
                                (point_b[1] - point_a[1])*(point_c[0] - point_a[0]))
            total_area += abs(f(col[0],vertex,col[i+1]))
        return total_area * 6371008.8 * 6371008.8
    
@annotate("string->double")
class Mypolygon_Perimeter(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self,col):
        import re
        from math import radians, cos, sin, sqrt, asin
        col = col[3:-3]
        #col = re.split(r'\],\s*\[|,', col)
        col = re.split(r'[,\[\]\s]+', col)
        col = [item for item in col if item]  
        len_ls = len(col)
        # assert len_ls % 2 == 0,'warning info_ls is not even'
        if len_ls % 2 != 0:
            col = [x for x in col if x != '0.0']
            len_ls = len(col)
        if len_ls < 2:
            return 0
        col = [(radians((float(col[i])) * cos(radians(float(col[i+1])))), radians(float(col[i+1]))) for i in range(0,len_ls,2)]
        perimeter = 0
        col = col + [col[0]]
        for i in range(len(col)-1):
            lon1, lat1, lon2, lat2 = map(radians, [float(col[i][0]), float(col[i][1]), float(col[i+1][0]), float(col[i+1][1])])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            perimeter += c
        return perimeter * 6371008.8  #6378137.0

@annotate("string,string->double")
class Mypolygon_Center(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self,col,cor):
        import re
        import math
        col = col[3:-3]
        col = re.split(r'[,\[\]\s]+', col)
        col = [item for item in col if item]      
        # col = re.split(r'\],\s*\[|,', col)
        len_ls = len(col)
        # assert len_ls % 2 == 0,'warning info_ls is not even'
        if len_ls % 2 != 0:
            col = [x for x in col if x != '0.0']
            len_ls = len(col)
        if len_ls < 2:    
            return 0

        col = [(float(col[i]),float(col[i+1])) for i in range(0,len_ls,2)]
        x = sum([i[0] for i in col])/len(col)
        y = sum([i[1] for i in col])/len(col)
        res = 0
        if cor=='lat':
            res = y 
        if cor=='lon':
            res = x
        return res

#### calculate the grid_index for each polygon center (x, y) 
#### Input:
# x: double
# y: double
# x_min: min x/longtitude of the range, double
# x_max: max x/longtitude of the range, double
# y_min: min y/latitude of the range, double
# y_max: max y/latitude of the range, double
# res: resolution, int
#### Output:
# grid index for the polygon center (x, y), int

@annotate("double,double,double,double,double,double,double->bigint")
class grid_index_cal(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, x, y, x_min, x_max, y_min, y_max, res):
        import re
        import math
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            # raise ValueError("the point is not in the given range")
            # print("the point is not in the given range")
            return -1
        
        # calculate the grid_index
        grid_x = int((x - x_min) / res)
        grid_y = int((y - y_min) / res)
        
        return grid_y * int((x_max - x_min) / res) + grid_x


"""
UDF for grid
"""
#### generate the EPSG4326 grid geometry based on given range of longtitude and latitude, and grid index and resolution
@annotate("bigint,double,double,double,double,double->string")
class grid_geometry_gen(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, grid_id, x_min, x_max, y_min, y_max, res):
        import re
        import math
        
        # calculate the grid relevant coordinate
        length = int((x_max - x_min) / res)
        x = int(grid_id % length) * res + x_min
        y = int(grid_id / length) * res + y_min

        # create the geometry on EPSG4326
        geometry = [
                    [x, y],
                    [x, y+res],
                    [x+res, y+res],
                    [x+res, y],
                    [x, y]
                ]
        
        return str(geometry)

#### convert and calculate the EPSG3857 grid geometry to EPSG4326
@annotate("int,double,double,double,double,int->string")
class grid_geometry_cal(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, grid_id, x_min, x_max, y_min, y_max, res):
        import re
        import math
        
        # calculate the grid relevant coordinate
        length = int((x_max - x_min) / res)
        x = int(grid_id % length) * res + x_min
        y = int(grid_id / length) * res + y_min

        def epsg3857_2_epsg4326(x, y):
            R = 6378137  # radius of the earth
            lon = (x / R) * (180 / math.pi)  # lon
            lat = math.degrees(math.atan(math.sinh(y / R)))  # lat
            return [lon, lat]

        # create the geometry in EPSG4326
        geometry = [
                    epsg3857_2_epsg4326(x, y),
                    epsg3857_2_epsg4326(x, y+res),
                    epsg3857_2_epsg4326(x+res, y+res),
                    epsg3857_2_epsg4326(x+res, y),
                    epsg3857_2_epsg4326(x, y)
                ]
        
        return str(geometry)           



@annotate("string,string->double")
class grid_coordinate(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, col, cor_type):
        import re
        import math
        col = eval(col)
        lon_ls = [col[i][0] for i in range(len(col))]
        lat_ls = [col[i][1] for i in range(len(col))]
        if cor_type == 'x_min':
            return min(lon_ls)
        elif cor_type == 'x_max':
            return max(lon_ls)
        elif cor_type == 'y_min':
            return min(lat_ls)
        elif cor_type == 'y_max':
            return max(lat_ls)
        else:
            return -200


"""
UDF FOR ST_Polygon

Converts ODPS stored geometry format to ST_Polygon compatible input format.
:param geometry_str: String in ODPS format, e.g., "[[x1, y1], [x2, y2], ...]"
:return: ST_Polygon compatible string, e.g., "polygon ((x1 y1, x2 y2, ...))"
"""
@annotate("string->string")
class geometry2stpolygon(object):
    def __init__(self):
        sys.setdlopenflags(10)

    def evaluate(self, geometry_str):
        # try:
        # Convert string representation of list to actual list
        geometry_list = eval(geometry_str)

        # Build polygon string
        coordinates = ", ".join("{0} {1}".format(x, y) for x, y in geometry_list)
        polygon_str = "polygon ((" + coordinates + "))"

        return polygon_str
