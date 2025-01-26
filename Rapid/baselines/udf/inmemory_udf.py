
def polygon_area(col):
    import re
    from math import radians, cos, sin, sqrt
    col = col[3:-3]
    col = re.split(r'\],\s*\[|,', col)
    len_ls = len(col)
    assert len_ls % 2 == 0,'warning info_ls is not even'
    #x = radians(coords[0]) * cos(radians(coords[1]))
    #y = radians(coords[1])
    col = [(radians((float(col[i])) * cos(radians(float(col[i+1])))), radians(float(col[i+1]))) for i in range(0,len_ls,2)]
    total_area = 0
    for i,vertex in enumerate(col[1:-1],start=1):
        f = lambda point_a, point_b, point_c:  0.5*((point_b[0] - point_a[0])*(point_c[1] - point_a[1]) -
                            (point_b[1] - point_a[1])*(point_c[0] - point_a[0]))
        total_area += abs(f(col[0],vertex,col[i+1]))
    return total_area * 6371008.8 * 6371008.8
    

def polygon_perimeter(col):
    import re
    from math import radians, cos, sin, sqrt, asin
    col = col[3:-3]
    col = re.split(r'\],\s*\[|,', col)
    len_ls = len(col)
    assert len_ls % 2 == 0,'warning info_ls is not even'
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


def polygon_center(col, cor):
    import re
    import math
    col = col[3:-3]
    col = re.split(r'\],\s*\[|,', col)
    len_ls = len(col)
    assert len_ls % 2 == 0,'warning info_ls is not even'
    col = [(float(col[i]),float(col[i+1])) for i in range(0,len_ls,2)]
    x = sum([i[0] for i in col])/len(col)
    y = sum([i[1] for i in col])/len(col)
    res = 0
    if cor=='lat':
        res = y 
    if cor=='lon':
        res = x
    return res


def grid_index_cal(x, y, x_min, x_max, y_min, y_max, res):
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



def grid_geometry_gen(grid_id, x_min, x_max, y_min, y_max, res):
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

