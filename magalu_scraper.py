import requests
import json
import csv
import time
from datetime import datetime
import os
import re

class MagaluScraper:
    def __init__(self):
        """Scraper Magazine Luiza usando apenas requests"""
        self.session = requests.Session()
        
        # Headers para simular navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        self.results = []
        print("✅ Scraper inicializado")
    
    def read_products_list(self, file_path):
        """Lê lista de produtos do CSV"""
        products = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                header = next(reader, None)  # Pula cabeçalho
                
                for row in reader:
                    if row and row[0].strip():
                        products.append(row[0].strip())
            
            print(f"📋 {len(products)} produtos carregados")
            return products
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")
            return []
    
    def search_product(self, product_name):
        """Busca produto no Magazine Luiza"""
        try:
            print(f"🔍 Buscando: {product_name}")
            
            # URL de busca
            search_url = f"https://www.magazineluiza.com.br/busca/{product_name.replace(' ', '+')}"
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # Encontra link do primeiro produto
                product_url = self.find_product_url(html)
                
                if product_url:
                    return self.extract_product_info(product_url, product_name)
                else:
                    return self.create_empty_result(product_name, "Produto não encontrado")
            
            else:
                return self.create_empty_result(product_name, f"Erro HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return self.create_empty_result(product_name, "Erro na busca")
    
    def find_product_url(self, html):
        """Encontra URL do primeiro produto"""
        patterns = [
            r'href="(/p/[^"]+)"',
            r'href="(https://www\.magazineluiza\.com\.br/p/[^"]+)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                url = matches[0]
                if not url.startswith('http'):
                    url = f"https://www.magazineluiza.com.br{url}"
                return url
        
        return None
    
    def extract_product_info(self, product_url, search_term):
        """Extrai informações do produto"""
        try:
            response = self.session.get(product_url, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                result = {
                    'produto_buscado': search_term,
                    'modelo': self.extract_name(html),
                    'preco_original': self.extract_original_price(html),
                    'preco_oferta': self.extract_sale_price(html),
                    'disponivel': self.check_availability(html),
                    'vendido_por': self.extract_seller(html),
                    'e_magalu': self.is_magalu_seller(html),
                    'url': product_url,
                    'data_consulta': datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                
                print(f"✅ {result['modelo'][:40]}...")
                print(f"💰 {result['preco_oferta']}")
                print(f"🏪 {result['vendido_por']}")
                
                return result
                
            else:
                return self.create_empty_result(search_term, "Erro ao acessar produto")
                
        except Exception as e:
            return self.create_empty_result(search_term, "Erro na extração")
    
    def extract_name(self, html):
        """Extrai nome do produto"""
        patterns = [
            r'<h1[^>]*data-testid="heading-product-title"[^>]*>([^<]+)</h1>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'"name":\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 10:
                    return name
        
        return "Produto encontrado"
    
    def extract_original_price(self, html):
        """Extrai preço original"""
        patterns = [
            r'data-testid="price-original"[^>]*>.*?R\$\s*([\d.,]+)',
            r'"originalPrice":\s*"?(\d+\.?\d*)"?',
            r'de:\s*R\$\s*([\d.,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                price = match.group(1).replace('.', '').replace(',', '.')
                try:
                    price_float = float(price)
                    if price_float > 10:
                        return f"R$ {price_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except:
                    continue
        
        return "N/A"
    
    def extract_sale_price(self, html):
        """Extrai preço de oferta"""
        patterns = [
            r'data-testid="price-value"[^>]*>.*?R\$\s*([\d.,]+)',
            r'"salePrice":\s*"?(\d+\.?\d*)"?',
            r'por:\s*R\$\s*([\d.,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                price = match.group(1).replace('.', '').replace(',', '.')
                try:
                    price_float = float(price)
                    if price_float > 10:
                        return f"R$ {price_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except:
                    continue
        
        return "N/A"
    
    def check_availability(self, html):
        """Verifica disponibilidade"""
        unavailable_patterns = [
            r'produto indisponível',
            r'fora de estoque',
            r'esgotado'
        ]
        
        for pattern in unavailable_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                return False
        
        return True
    
    def extract_seller(self, html):
        """Extrai vendedor"""
        patterns = [
            r'Vendido e entregue por:?\s*([^<\n]+)',
            r'Vendido por:?\s*([^<\n]+)',
            r'"seller":\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                seller = match.group(1).strip()
                if seller and len(seller) > 2:
                    return seller
        
        return "Magazine Luiza"
    
    def is_magalu_seller(self, html):
        """Verifica se é vendido pela Magalu"""
        magalu_indicators = [
            r'vendido e entregue por magazine luiza',
            r'vendido por magazine luiza',
            r'vendido.*magalu'
        ]
        
        html_lower = html.lower()
        
        for pattern in magalu_indicators:
            if re.search(pattern, html_lower):
                return True
        
        # Se não menciona vendedor específico, assume Magalu
        if not re.search(r'vendido por(?!.*magazine|.*magalu)', html_lower):
            return True
        
        return False
    
    def create_empty_result(self, search_term, status):
        """Cria resultado vazio"""
        return {
            'produto_buscado': search_term,
            'modelo': status,
            'preco_original': 'N/A',
            'preco_oferta': 'N/A',
            'disponivel': False,
            'vendido_por': 'N/A',
            'e_magalu': False,
            'url': 'N/A',
            'data_consulta': datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    
    def process_products(self, file_path):
        """Processa lista de produtos"""
        try:
            products = self.read_products_list(file_path)
            
            if not products:
                print("❌ Nenhum produto para processar")
                return
            
            print(f"🚀 Processando {len(products)} produtos...")
            print("-" * 60)
            
            for i, product in enumerate(products, 1):
                print(f"\n📦 [{i}/{len(products)}] {product}")
                
                result = self.search_product(product)
                self.results.append(result)
                
                # Pausa entre produtos
                time.sleep(2)
            
            self.save_results()
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
    
    def save_results(self):
        """Salva resultados em CSV"""
        try:
            if not self.results:
                print("❌ Nenhum resultado para salvar")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"magalu_busca_{timestamp}.csv"
            
            fieldnames = [
                'produto_buscado', 'modelo', 'preco_original', 'preco_oferta', 
                'disponivel', 'vendido_por', 'e_magalu', 'data_consulta', 'url'
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.results:
                    writer.writerow(result)
            
            # Estatísticas
            total = len(self.results)
            encontrados = len([r for r in self.results if 'erro' not in r['modelo'].lower()])
            magalu_count = len([r for r in self.results if r.get('e_magalu', False)])
            
            print(f"\n📊 RESUMO:")
            print(f"✅ Total processados: {total}")
            print(f"🎯 Produtos encontrados: {encontrados}")
            print(f"🏪 Vendidos pela Magalu: {magalu_count}")
            print(f"💾 Arquivo salvo: {filename}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

def main():
    """Função principal"""
    print("🛒 MAGAZINE LUIZA SCRAPER")
    print("=" * 40)
    
    # Verifica se arquivo existe
    if not os.path.exists("lista_produtos.csv"):
        print("❌ Arquivo 'lista_produtos.csv' não encontrado")
        print("📝 Crie o arquivo com uma coluna 'produto'")
        return
    
    try:
        scraper = MagaluScraper()
        scraper.process_products("lista_produtos.csv")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("🎉 Concluído!")

if __name__ == "__main__":
    main()