import csv
from collections import defaultdict

# Column indices (0-based)
# codi_barri: 4
# barrio_nombre: 1
# distrito_nombre: 2
# anio: 8
# precio: 9

file_path = 'data/exports/looker_studio/master_table_barcelona_housing.csv'
affected_barrios = ['12', '42', '47', '56', '58']

barrio_prices = defaultdict(list)
district_prices = defaultdict(lambda: defaultdict(list))
barrio_to_district = {}
barrio_names = {}

with open(file_path, mode='r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        try:
            codi = row[4]
            name = row[1]
            dist = row[2]
            anio = int(row[8])
            price_str = row[9]
            
            if not price_str:
                continue
            price = float(price_str)
            
            if anio >= 2014:
                if codi in affected_barrios:
                    barrio_prices[codi].append(price)
                    barrio_to_district[codi] = dist
                    barrio_names[codi] = name
                
                # Keep track of all district prices by year to calculate district average correctly
                district_prices[dist][anio].append(price)
        except (ValueError, IndexError):
            continue

print("--- FACTORES DE AJUSTE CALCULADOS ---")
print(f"{'Barrio':<30} | {'Avg Barrio':<10} | {'Avg Distrito':<12} | {'Ratio'}")
print("-" * 75)

for codi in affected_barrios:
    if codi not in barrio_prices:
        print(f"⚠️ {codi}: No data found after 2013.")
        continue
    
    dist = barrio_to_district[codi]
    name = barrio_names[codi]
    
    # Calculate average of the barrio
    avg_barrio = sum(barrio_prices[codi]) / len(barrio_prices[codi])
    
    # Calculate average of the district (average of yearly district averages)
    yearly_dist_avgs = []
    for anio in range(2014, 2026): # 2014-2025
        if anio in district_prices[dist]:
            prices = district_prices[dist][anio]
            yearly_dist_avgs.append(sum(prices) / len(prices))
    
    if yearly_dist_avgs:
        avg_dist = sum(yearly_dist_avgs) / len(yearly_dist_avgs)
        ratio = avg_barrio / avg_dist
        print(f"{name:<30} | {avg_barrio:>10.2f} | {avg_dist:>12.2f} | {ratio:.4f}")
    else:
        print(f"⚠️ {name}: No district data found.")
