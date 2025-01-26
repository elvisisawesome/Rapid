#include <mysql.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// earth radius and PI
#define EARTH_RADIUS 6371008.8
#define M_PI 3.14159265358979323846

// Helper function: Convert degrees to radians
double radians(double degrees) {
    return degrees * M_PI / 180.0;
}

// Helper function: Parse input string to double array
int parse_coordinates(const char* input, double** coords) {
    // Find the first '[' and the last ']'
    const char* start = strchr(input, '[');
    const char* end = strrchr(input, ']');
    if (!start || !end || start >= end) {
        return 0;
    }

    // Skip the outermost '[' and trim ending ']'
    start += 2;  // Skip '[['
    end -= 2;    // Remove ']]'
    int length = end - start + 1;

    char* buffer = (char*)malloc(length + 1);
    strncpy(buffer, start, length);
    buffer[length] = '\0';  // Null-terminate the buffer

    // Remove all '[' and ']' from the string
    for (char* p = buffer; *p; ++p) {
        if (*p == '[' || *p == ']') {
            *p = ' ';
        }
    }

    // Count commas to determine the number of values
    int count = 0;
    for (char* p = buffer; *p; ++p) {
        if (*p == ',') count++;
    }
    count++;  // Add 1 for the last value after the last comma

    // Allocate memory for the double array
    *coords = (double*)malloc(count * sizeof(double));

    // Parse the numbers from the cleaned string
    char* token = strtok(buffer, ",");
    int i = 0;
    while (token) {
        (*coords)[i++] = atof(token);
        token = strtok(NULL, ",");
    }

    free(buffer);
    return count;
}

// UDF to calculate polygon area
_Bool polygon_area_init(UDF_INIT* initid, UDF_ARGS* args, char* message) {
    if (args->arg_count != 1 || args->arg_type[0] != STRING_RESULT) {
        strcpy(message, "polygon_area expects a single string argument.");
        return 1;
    }
    return 0;
}

double polygon_area(UDF_INIT* initid, UDF_ARGS* args, char* is_null, char* error) {
    const char* input = args->args[0];
    double* coords = NULL;
    int count = parse_coordinates(input, &coords);

    if (count < 6 || count % 2 != 0) {  // Must have at least 3 points
        free(coords);
        return 0;
    }

    int num_points = count / 2;
    double area = 0.0;

    // Convert to radians and calculate the area
    double* x = (double*)malloc(num_points * sizeof(double));
    double* y = (double*)malloc(num_points * sizeof(double));

    for (int i = 0; i < num_points; i++) {
        x[i] = radians(coords[2 * i]) * cos(radians(coords[2 * i + 1]));
        y[i] = radians(coords[2 * i + 1]);
    }

    for (int i = 1; i < num_points - 1; i++) {
        double ax = x[0], ay = y[0];
        double bx = x[i], by = y[i];
        double cx = x[i + 1], cy = y[i + 1];
        area += fabs(0.5 * ((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)));
    }

    free(coords);
    free(x);
    free(y);

    return area * EARTH_RADIUS * EARTH_RADIUS;
}

void polygon_area_deinit(UDF_INIT* initid) {}

// UDF to calculate polygon perimeter
_Bool polygon_perimeter_init(UDF_INIT* initid, UDF_ARGS* args, char* message) {
    if (args->arg_count != 1 || args->arg_type[0] != STRING_RESULT) {
        strcpy(message, "polygon_perimeter expects a single string argument.");
        return 1;
    }
    return 0;
}

double polygon_perimeter(UDF_INIT* initid, UDF_ARGS* args, char* is_null, char* error) {
    const char* input = args->args[0];
    double* coords = NULL;
    int count = parse_coordinates(input, &coords);

    if (count < 6 || count % 2 != 0) {  // Must have at least 3 points
        free(coords);
        return 0;
    }

    int num_points = count / 2;
    double perimeter = 0.0;

    // Add the first point to the end to close the polygon
    double* x = (double*)malloc((num_points + 1) * sizeof(double));
    double* y = (double*)malloc((num_points + 1) * sizeof(double));

    for (int i = 0; i < num_points; i++) {
        x[i] = radians(coords[2 * i]) * cos(radians(coords[2 * i + 1]));
        y[i] = radians(coords[2 * i + 1]);
    }
    x[num_points] = x[0];
    y[num_points] = y[0];

    for (int i = 0; i < num_points; i++) {
        double dx = x[i + 1] - x[i];
        double dy = y[i + 1] - y[i];
        perimeter += sqrt(dx * dx + dy * dy);
    }

    free(coords);
    free(x);
    free(y);

    return perimeter * EARTH_RADIUS;
}

void polygon_perimeter_deinit(UDF_INIT* initid) {}

// UDF to calculate polygon center
_Bool polygon_center_init(UDF_INIT* initid, UDF_ARGS* args, char* message) {
    if (args->arg_count != 2 || args->arg_type[0] != STRING_RESULT || args->arg_type[1] != STRING_RESULT) {
        strcpy(message, "polygon_center expects two string arguments.");
        return 1;
    }
    return 0;
}

double polygon_center(UDF_INIT* initid, UDF_ARGS* args, char* is_null, char* error) {
    const char* input = args->args[0];
    const char* cor = args->args[1];
    double* coords = NULL;
    int count = parse_coordinates(input, &coords);

    if (count < 6 || count % 2 != 0) {  // Must have at least 3 points
        free(coords);
        return 0;
    }

    int num_points = count / 2;
    double sum_x = 0.0, sum_y = 0.0;

    for (int i = 0; i < num_points; i++) {
        sum_x += coords[2 * i];
        sum_y += coords[2 * i + 1];
    }

    double result = 0.0;
    if (strcmp(cor, "lat") == 0) {
        result = sum_y / num_points;
    } else if (strcmp(cor, "lon") == 0) {
        result = sum_x / num_points;
    }

    free(coords);
    return result;
}

void polygon_center_deinit(UDF_INIT* initid) {}

// calculate the grid index
// UDF initialization
_Bool grid_index_cal_init(UDF_INIT* initid, UDF_ARGS* args, char* message) {
    if (args->arg_count != 7) {
        strcpy(message, "grid_index_cal requires exactly 7 arguments: x, y, x_min, x_max, y_min, y_max, res");
        return 1;
    }
    for (int i = 0; i < 7; i++) {
        if (args->arg_type[i] != REAL_RESULT) {
            strcpy(message, "All arguments for grid_index_cal must be of type DOUBLE");
            return 1;
        }
    }
    return 0;
}

// UDF main function
long long grid_index_cal(UDF_INIT* initid, UDF_ARGS* args, char* is_null, char* error) {
    double x = *((double*)args->args[0]);
    double y = *((double*)args->args[1]);
    double x_min = *((double*)args->args[2]);
    double x_max = *((double*)args->args[3]);
    double y_min = *((double*)args->args[4]);
    double y_max = *((double*)args->args[5]);
    double res = *((double*)args->args[6]);

    // Check if the point is within range
    if (!(x_min <= x && x <= x_max && y_min <= y && y <= y_max)) {
        return -1;
    }

    // Calculate grid index
    int grid_x = (int)((x - x_min) / res);
    int grid_y = (int)((y - y_min) / res);

    int grid_width = (int)((x_max - x_min) / res);

    return grid_y * grid_width + grid_x;
}

// UDF deinitialization
void grid_index_cal_deinit(UDF_INIT* initid) {}

// generate the grid geometry
// UDF initialization
_Bool grid_geometry_gen_init(UDF_INIT* initid, UDF_ARGS* args, char* message) {
    if (args->arg_count != 6) {
        strcpy(message, "grid_geometry_gen requires exactly 6 arguments: grid_id, x_min, x_max, y_min, y_max, res");
        return 1;
    }
    if (args->arg_type[0] != INT_RESULT || args->arg_type[1] != REAL_RESULT || args->arg_type[2] != REAL_RESULT ||
        args->arg_type[3] != REAL_RESULT || args->arg_type[4] != REAL_RESULT || args->arg_type[5] != REAL_RESULT) {
        strcpy(message, "grid_geometry_gen arguments must be of types INT, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE");
        return 1;
    }
    initid->maybe_null = 1;  // Result may be NULL
    return 0;
}

// UDF main function
char* grid_geometry_gen(UDF_INIT* initid, UDF_ARGS* args, char* result, unsigned long* length, char* is_null, char* error) {
    int grid_id = *((int*)args->args[0]);
    double x_min = *((double*)args->args[1]);
    double x_max = *((double*)args->args[2]);
    double y_min = *((double*)args->args[3]);
    double y_max = *((double*)args->args[4]);
    double res = *((double*)args->args[5]);

    // Calculate grid width
    int grid_width = (int)((x_max - x_min) / res);

    // Calculate x and y coordinates
    double x = (grid_id % grid_width) * res + x_min;
    double y = (grid_id / grid_width) * res + y_min;

    // Generate geometry string
    char geometry[256];
    snprintf(geometry, sizeof(geometry),
             "[[%f, %f], [%f, %f], [%f, %f], [%f, %f], [%f, %f]]",
             x, y, x, y + res, x + res, y + res, x + res, y, x, y);

    // Copy result to output
    *length = strlen(geometry);
    strncpy(result, geometry, *length);
    return result;
}

// UDF deinitialization
void grid_geometry_gen_deinit(UDF_INIT* initid) {}