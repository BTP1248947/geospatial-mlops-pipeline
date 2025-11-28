
import json
import os

def create_geojson(name, min_lon, min_lat, max_lon, max_lat, region_name):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"region": region_name},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat],
                        [max_lon, min_lat],
                        [max_lon, max_lat],
                        [min_lon, max_lat],
                        [min_lon, min_lat]
                    ]]
                }
            }
        ]
    }
    
    filename = f"aoi/{name}.geojson"
    with open(filename, 'w') as f:
        json.dump(geojson, f, indent=2)
    print(f"Created {filename}")

def main():
    # 1. Novo Progresso, Para, Brazil (Amazon)
    # Center: -7.15, -55.40. Size: 0.2 deg (~22km)
    create_geojson("brazil_novo_progresso", -55.50, -7.25, -55.30, -7.05, "novo_progresso")

    # 2. Altamira, Para, Brazil (Amazon)
    # Center: -3.20, -52.20
    create_geojson("brazil_altamira", -52.30, -3.30, -52.10, -3.10, "altamira")

    # 3. Porto Velho, Rondonia, Brazil (Amazon)
    # Center: -8.76, -63.90
    create_geojson("brazil_porto_velho", -64.00, -8.86, -63.80, -8.66, "porto_velho")

    # 4. Riau, Sumatra, Indonesia (Palm Oil)
    # Center: 0.50, 101.45
    create_geojson("indonesia_riau", 101.35, 0.40, 101.55, 0.60, "riau")

    # 5. Central Kalimantan, Indonesia (Mining/Palm Oil)
    # Center: -2.20, 113.90
    create_geojson("indonesia_kalimantan", 113.80, -2.30, 114.00, -2.10, "kalimantan")

if __name__ == "__main__":
    main()
