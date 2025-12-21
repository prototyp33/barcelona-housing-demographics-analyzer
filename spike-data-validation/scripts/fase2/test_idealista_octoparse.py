#!/usr/bin/env python3
"""
Test del código exacto del artículo Octoparse para Idealista.

Basado en: https://www.octoparse.es/blog/como-extraer-los-datos-de-idealista-con-web-scraping

Este script prueba el código exacto del artículo para verificar si funciona.
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

# URL de prueba (primero Madrid del artículo, luego Gràcia)
url_madrid = 'https://www.idealista.com/en/venta-viviendas/madrid-madrid/'
url_gracia = 'https://www.idealista.com/venta-viviendas/barcelona/gracia/'

# Headers exactos del artículo
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_url(url: str, name: str) -> bool:
    """Prueba una URL específica."""
    print(f"\n{'='*70}")
    print(f"Probando: {name}")
    print(f"URL: {url}")
    print('='*70)
    
    try:
        # Make the request (código exacto del artículo)
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status code: {response.status_code}")
        
        # Check response status
        if response.status_code == 200:
            # Parse the page content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all property listing items (código exacto del artículo)
            listings = soup.find_all('article', class_='item')
            
            print(f"Listings encontrados: {len(listings)}")
            
            if len(listings) == 0:
                # Intentar otros selectores alternativos
                print("\nIntentando selectores alternativos...")
                listings_alt1 = soup.find_all('article')
                print(f"  article (sin clase): {len(listings_alt1)}")
                
                listings_alt2 = soup.find_all('div', class_='item')
                print(f"  div.item: {len(listings_alt2)}")
                
                listings_alt3 = soup.find_all('div', {'class': 'item'})
                print(f"  div[class='item']: {len(listings_alt3)}")
                
                # Si encontramos con alternativos, usar esos
                if listings_alt1:
                    listings = listings_alt1[:10]  # Limitar para test
                elif listings_alt2:
                    listings = listings_alt2[:10]
                elif listings_alt3:
                    listings = listings_alt3[:10]
            
            if len(listings) > 0:
                print(f"\n✅ Encontrados {len(listings)} listings")
                print("\nExtrayendo datos de los primeros 3...")
                
                # Extract data for each property (código exacto del artículo)
                for i, listing in enumerate(listings[:3], 1):
                    print(f"\n--- Listing {i} ---")
                    
                    # Get the property title
                    title_elem = listing.find('a', class_='item-link')
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    
                    # Get the property price
                    price_elem = listing.find('span', class_='item-price')
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"
                    
                    # Get the property location
                    location_elem = listing.find('span', class_='item-detail')
                    location = location_elem.get_text(strip=True) if location_elem else "N/A"
                    
                    # Print the data
                    print(f'Title: {title}')
                    print(f'Price: {price}')
                    print(f'Location: {location}')
                
                return True
            else:
                print("\n❌ No se encontraron listings")
                print("\nInspeccionando estructura HTML...")
                print(f"Tamaño HTML: {len(response.content)} bytes")
                
                # Buscar elementos comunes
                all_articles = soup.find_all('article')
                all_divs_with_item = soup.find_all('div', class_=lambda x: x and 'item' in x.lower())
                
                print(f"Total <article>: {len(all_articles)}")
                print(f"Total <div> con 'item' en clase: {len(all_divs_with_item)}")
                
                # Guardar HTML para inspección
                with open('test_idealista_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("\n📄 HTML guardado en: test_idealista_response.html")
                
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            if response.status_code == 403:
                print("   Bloqueado por protección anti-bot")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("TEST CÓDIGO EXACTO ARTÍCULO OCTOPARSE")
    print("="*70)
    
    # Probar primero Madrid (URL del ejemplo del artículo)
    success_madrid = test_url(url_madrid, "Madrid (ejemplo artículo)")
    
    # Probar luego Gràcia (nuestro objetivo)
    success_gracia = test_url(url_gracia, "Gràcia (nuestro objetivo)")
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Madrid: {'✅ OK' if success_madrid else '❌ Falló'}")
    print(f"Gràcia: {'✅ OK' if success_gracia else '❌ Falló'}")
    
    if not success_madrid and not success_gracia:
        print("\n⚠️  Ambas URLs fallaron. Posibles causas:")
        print("   1. Idealista ha reforzado protección desde el artículo")
        print("   2. IP puede estar bloqueada")
        print("   3. Headers necesitan actualización")
        print("   4. Estructura HTML cambió")

