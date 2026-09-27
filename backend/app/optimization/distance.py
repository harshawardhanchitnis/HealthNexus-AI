from math import asin, cos, radians, sin, sqrt


def haversine(lat1, lon1, lat2, lon2):
    if not all(-90 <= x <= 90 for x in (lat1, lat2)) or not all(-180 <= x <= 180 for x in (lon1, lon2)):
        raise ValueError("Invalid coordinates")
    a, b = radians(lat1), radians(lat2)
    h = sin((b-a)/2)**2 + cos(a)*cos(b)*sin(radians(lon2-lon1)/2)**2
    return 6371.0088 * 2 * asin(sqrt(min(1., h)))
