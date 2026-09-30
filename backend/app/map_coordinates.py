"""Display-only prototype district centres, never operational/solver coordinates.

Rounded project-owned illustrative anchors near district administrative centres,
not surveyed centroids or hospital locations. Catalogue covers existing Indian
prototype districts only. SHA-256 offsets are stable across processes/profiles.
Other countries have no district catalogue and retain their illustrative points.
"""
from hashlib import sha256
from math import cos, pi, radians, sin, sqrt

VERSION = 'illustrative-district-v1'
# (latitude, longitude); map-only and deliberately approximate.
DISTRICT_CENTRES = {
    'AP-GUNTUR': (16.30, 80.44), 'AP-VISAKHAPATNAM': (17.69, 83.22),
    'AR-TAWANG': (27.59, 91.87), 'AR-LOWER-SUBANSIRI': (27.55, 93.83),
    'AS-KAMRUP-METROPOLITAN': (26.15, 91.74), 'AS-DIBRUGARH': (27.47, 94.91),
    'BR-PATNA': (25.61, 85.14), 'BR-GAYA': (24.79, 85.00),
    'CG-RAIPUR': (21.25, 81.63), 'CG-BILASPUR': (22.08, 82.14),
    'GA-NORTH-GOA': (15.49, 73.83), 'GA-SOUTH-GOA': (15.28, 73.96),
    'GJ-AHMEDABAD': (23.02, 72.57), 'GJ-SURAT': (21.17, 72.83),
    'HR-GURUGRAM': (28.46, 77.03), 'HR-HISAR': (29.15, 75.72),
    'HP-SHIMLA': (31.10, 77.17), 'HP-KANGRA': (32.10, 76.27),
    'JH-RANCHI': (23.34, 85.31), 'JH-DHANBAD': (23.80, 86.43),
    'KA-BENGALURU-URBAN': (12.97, 77.59), 'KA-MYSURU': (12.30, 76.64),
    'KL-THIRUVANANTHAPURAM': (8.52, 76.94), 'KL-ERNAKULAM': (9.98, 76.30),
    'MP-BHOPAL': (23.26, 77.41), 'MP-INDORE': (22.72, 75.86),
    'MH-PUNE': (18.53, 73.85), 'MH-NAGPUR': (21.15, 79.09),
    'MN-IMPHAL-WEST': (24.82, 93.94), 'MN-THOUBAL': (24.64, 94.01),
    'ML-EAST-KHASI-HILLS': (25.57, 91.88), 'ML-WEST-GARO-HILLS': (25.51, 90.22),
    'MZ-AIZAWL': (23.73, 92.72), 'MZ-LUNGLEI': (22.89, 92.75),
    'NL-KOHIMA': (25.67, 94.11), 'NL-MOKOKCHUNG': (26.32, 94.52),
    'OD-KHORDHA': (20.18, 85.62), 'OD-CUTTACK': (20.46, 85.88),
    'PB-LUDHIANA': (30.90, 75.86), 'PB-AMRITSAR': (31.63, 74.87),
    'RJ-JAIPUR': (26.91, 75.79), 'RJ-JODHPUR': (26.24, 73.02),
    'SK-GANGTOK': (27.33, 88.61), 'SK-NAMCHI': (27.17, 88.36),
    'TN-CHENNAI': (13.08, 80.27), 'TN-COIMBATORE': (11.02, 76.96),
    'TS-HYDERABAD': (17.39, 78.49), 'TS-NIZAMABAD': (18.67, 78.09),
    'TR-WEST-TRIPURA': (23.83, 91.28), 'TR-GOMATI': (23.53, 91.49),
    'UP-LUCKNOW': (26.85, 80.95), 'UP-VARANASI': (25.32, 82.97),
    'UK-DEHRADUN': (30.32, 78.03), 'UK-HARIDWAR': (29.95, 78.16),
    'WB-KOLKATA': (22.57, 88.36), 'WB-HOWRAH': (22.59, 88.26),
    'AN-SOUTH-ANDAMAN': (11.67, 92.74), 'AN-NICOBAR': (9.17, 92.82),
    'CH-CHANDIGARH': (30.73, 76.78),
    'DN-DADRA-AND-NAGAR-HAVELI': (20.27, 73.02), 'DN-DAMAN': (20.40, 72.83),
    'DL-NEW-DELHI': (28.61, 77.21), 'JK-JAMMU': (32.73, 74.86),
    'JK-SRINAGAR': (34.08, 74.80), 'LA-LEH': (34.15, 77.58),
    'LA-KARGIL': (34.55, 76.13), 'LD-LAKSHADWEEP': (10.57, 72.64),
    'PY-PUDUCHERRY': (11.94, 79.81), 'PY-KARAIKAL': (10.93, 79.84),
}


def map_coordinates(facility):
    """GeoJSON longitude/latitude; bounded 0.5–3 km illustrative offset."""
    if facility.country_id != 'IN':
        return [facility.longitude, facility.latitude]
    # Never silently put an Indian district at its legacy state-centred point.
    lat, lon = DISTRICT_CENTRES[facility.district_id]
    digest = sha256(f'{VERSION}:{facility.id}'.encode()).digest()
    angle = int.from_bytes(digest[:8], 'big') / 2**64 * 2 * pi
    radius = 0.5 + 2.5 * sqrt(int.from_bytes(digest[8:16], 'big') / 2**64)
    return [round(lon + radius * cos(angle) / (111.195 * cos(radians(lat))), 6),
            round(lat + radius * sin(angle) / 111.195, 6)]
