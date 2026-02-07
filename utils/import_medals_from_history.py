# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - utils/import_medals_from_descriptions.py
# Importa medalhas do diretório descriptions para medals.json
# ===================================================================

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class MedalDescriptionImporter:
    """Importador de medalhas de arquivos JSON do diretório descriptions."""
    
    def __init__(self):
        """Inicializa o importador com caminhos automáticos."""
        # Detecta diretório do projeto
        self.project_root = Path(__file__).resolve().parents[1]
        self.medals_base = self.project_root / "app" / "assets" / "medals"
        
        # Diretórios de trabalho
        self.descriptions_dir = self.medals_base / "descriptions"
        self.output_file = self.medals_base / "meta" / "medals.json"
        self.images_dir = self.medals_base / "images"
        self.ribbons_dir = self.medals_base / "ribbons"
        
        # País padrão (pode ser alterado por medalha)
        self.default_country = "germany"
    
    def import_all(self) -> List[Dict[str, Any]]:
        """Importa todas as medalhas do diretório descriptions.
        
        Returns:
            Lista de dicionários de medalhas no formato simplificado
        """
        if not self.descriptions_dir.exists():
            logger.error(f"Diretório não encontrado: {self.descriptions_dir}")
            return []
        
        json_files = list(self.descriptions_dir.glob("*.json"))
        if not json_files:
            logger.warning(f"Nenhum arquivo JSON encontrado em {self.descriptions_dir}")
            return []
        
        logger.info(f"Encontrados {len(json_files)} arquivos JSON\n")
        
        medals: List[Dict[str, Any]] = []
        
        for json_file in sorted(json_files):
            try:
                logger.info(f"Processando: {json_file.name}")
                medal_dict = self._convert_to_simple_format(json_file)
                
                if medal_dict:
                    medals.append(medal_dict)
                    logger.info(f"  ✓ Importada: {medal_dict['nome']}")
                else:
                    logger.warning(f"  ✗ Ignorada (dados insuficientes)")
            
            except Exception as e:
                logger.error(f"  ✗ Erro: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Total de medalhas importadas: {len(medals)}")
        logger.info(f"{'='*60}\n")
        
        return medals
    
    def _convert_to_simple_format(self, json_file: Path) -> Optional[Dict[str, Any]]:
        """Converte JSON de descrição para formato simplificado do input_medals_tab.
        
        Args:
            json_file: Caminho do arquivo JSON de descrição
            
        Returns:
            Dicionário no formato simplificado ou None se inválido
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extrai campos básicos
        medal_id = data.get("id", "")
        nome = data.get("nome", "")
        resumo = data.get("resumo", "")
        
        if not medal_id or not nome:
            return None
        
        # Monta caminhos relativos
        imagem_path = f"images/{medal_id}.png"
        ribbon_path = f"ribbons/ribbon_{medal_id}.png"
        
        # Verifica existência de imagem (obrigatória)
        if not (self.images_dir / f"{medal_id}.png").exists():
            logger.warning(f"    ⚠ Imagem não encontrada: {medal_id}.png")
        
        # Ribbon é opcional
        if not (self.ribbons_dir / f"ribbon_{medal_id}.png").exists():
            logger.debug(f"    ⓘ Ribbon não encontrada (opcional): ribbon_{medal_id}.png")
            ribbon_path = ""
        
        # Extrai país (se disponível no JSON)
        country = self._extract_country(data) or self.default_country
        
        # Gera condições de conquista
        condicoes = self._generate_conditions(medal_id, data)
        
        return {
            "nome": nome,
            "imagem_path": imagem_path,
            "ribbon_path": ribbon_path,
            "descricao": resumo,
            "condicoes": condicoes,
            "country": country
        }
    
    def _extract_country(self, data: Dict[str, Any]) -> Optional[str]:
        """Tenta extrair o país da medalha dos dados históricos.
        
        Args:
            data: Dicionário com dados da medalha
            
        Returns:
            Código do país normalizado ou None
        """
        # Busca em campos comuns
        country_hints = [
            data.get("pais", ""),
            data.get("country", ""),
            data.get("origem", "")
        ]
        
        for hint in country_hints:
            normalized = self._normalize_country(hint)
            if normalized:
                return normalized
        
        # Busca em história/fundação
        historia = data.get("historia", {})
        if isinstance(historia, dict):
            fundacao = historia.get("fundacao", {}) or historia.get("criacao", {})
            if isinstance(fundacao, dict):
                local = fundacao.get("local", "")
                instituidor = fundacao.get("instituidor", "") or fundacao.get("fundador", "")
                
                combined = f"{local} {instituidor}".lower()
                
                if any(word in combined for word in ["pruss", "alemã", "german", "deutsch"]):
                    return "germany"
                if any(word in combined for word in ["franc", "french"]):
                    return "france"
                if any(word in combined for word in ["brit", "english", "inglês"]):
                    return "britain"
                if any(word in combined for word in ["belg", "belgium"]):
                    return "belgian"
                if any(word in combined for word in ["amer", "usa", "united states"]):
                    return "usa"
        
        return None
    
    @staticmethod
    def _normalize_country(country_str: str) -> Optional[str]:
        """Normaliza string de país para código válido.
        
        Args:
            country_str: String com nome do país
            
        Returns:
            Código normalizado ou None
        """
        s = (country_str or "").lower().strip()
        
        if not s:
            return None
        
        # Mapeamento de variações para códigos
        mapping = {
            "germany": ["germany", "alemanha", "deutschland", "german", "prussian", "prussia", "prússia"],
            "france": ["france", "frança", "french", "francês"],
            "britain": ["britain", "uk", "england", "inglaterra", "british", "britânico"],
            "usa": ["usa", "america", "américa", "united states", "eua"],
            "belgian": ["belgium", "belgian", "bélgica", "belga"]
        }
        
        for code, variations in mapping.items():
            if any(var in s for var in variations):
                return code
        
        return None
    
    def _generate_conditions(self, medal_id: str, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Gera condições de conquista baseadas no ID e dados históricos.
        
        Args:
            medal_id: ID da medalha
            data: Dicionário com dados históricos
            
        Returns:
            Lista de dicionários de condições
        """
        conditions: List[Dict[str, str]] = []
        
        # Pour le Mérite
        if "pour_le_merit" in medal_id or "blue_max" in medal_id:
            destaque = data.get("destaqueNaPrimeiraGuerra", {})
            if isinstance(destaque, dict):
                criterios = destaque.get("criteriosPilotos", {})
                if isinstance(criterios, dict):
                    inicial = criterios.get("inicial", "")
                    if inicial:
                        conditions.append({
                            "descricao": inicial,
                            "tipo": "victories",
                            "valor": "8"
                        })
                    
                    evolucao = criterios.get("evolucao", "")
                    if evolucao and "20" in evolucao:
                        conditions.append({
                            "descricao": "Critério tardio da guerra (1917-1918): 20 vitórias",
                            "tipo": "victories",
                            "valor": "20"
                        })
        
        # Cruz de Ferro
        elif "iron_cross" in medal_id or "cruz_de_ferro" in medal_id:
            classes = data.get("classes", [])
            if classes and isinstance(classes, list):
                for cls in classes[:3]:  # Primeiras 3 classes
                    if isinstance(cls, dict):
                        nome_classe = cls.get("nome", "")
                        criterio = cls.get("criterio", "")
                        conditions.append({
                            "descricao": f"{nome_classe}: {criterio}" if criterio else nome_classe,
                            "tipo": "combat",
                            "valor": "1"
                        })
        
        # Distintivo de Ferido
        elif "wound_badge" in medal_id or "ferido" in medal_id:
            classe_tipo = "black"
            if "silver" in medal_id or "prata" in medal_id:
                classe_tipo = "silver"
            elif "gold" in medal_id or "ouro" in medal_id:
                classe_tipo = "gold"
            
            classes = data.get("classes", [])
            if classes and isinstance(classes, list):
                for cls in classes:
                    if isinstance(cls, dict):
                        nome = cls.get("nome", "").lower()
                        if classe_tipo in nome or (classe_tipo == "black" and "preto" in nome):
                            criterio = cls.get("criterio", "")
                            conditions.append({
                                "descricao": criterio or f"Ferimento em combate ({nome})",
                                "tipo": "wounds",
                                "valor": cls.get("ferimentos", "1")
                            })
                            break
        
        # Ordem da Casa de Hohenzollern
        elif "hohenzollern" in medal_id:
            conditions.append({
                "descricao": "Serviços distinguidos à Casa Real Prussiana ou atos notáveis de bravura",
                "tipo": "service",
                "valor": "1"
            })
        
        # Distintivo de Piloto
        elif "pilot_badge" in medal_id or "distintivo_piloto" in medal_id:
            conditions.append({
                "descricao": "Conclusão bem-sucedida do treinamento de piloto militar",
                "tipo": "qualification",
                "valor": "1"
            })
        
        # Medalha de Mérito de Guerra Prussiana
        elif "war_merit" in medal_id or "merito_guerra" in medal_id:
            conditions.append({
                "descricao": "Serviços extraordinários durante a guerra",
                "tipo": "service",
                "valor": "1"
            })
        
        # Ordem Militar de Max Joseph (Baviera)
        elif "max_joseph" in medal_id or "bav_order" in medal_id:
            conditions.append({
                "descricao": "Ato de bravura excepcional que mudou o curso de uma batalha",
                "tipo": "heroism",
                "valor": "1"
            })
        
        # Ordem da Águia Vermelha
        elif "red_eagle" in medal_id or "aguia_vermelha" in medal_id:
            conditions.append({
                "descricao": "Serviços civis ou militares de alto mérito ao Estado Prussiano",
                "tipo": "service",
                "valor": "1"
            })
        
        # Genérico para medalhas não mapeadas
        else:
            nome = data.get("nome", "Medalha")
            conditions.append({
                "descricao": f"Condição de conquista para {nome} (a definir)",
                "tipo": "generic",
                "valor": "1"
            })
        
        return conditions
    
    def save_to_file(self, medals: List[Dict[str, Any]]) -> None:
        """Salva medalhas importadas no arquivo medals.json.
        
        Args:
            medals: Lista de medalhas a salvar
        """
        try:
            # Cria diretório meta se não existir
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva com formatação
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(medals, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Medalhas salvas em: {self.output_file}")
            logger.info(f"  Total de medalhas: {len(medals)}")
        
        except OSError as e:
            logger.error(f"✗ Erro ao salvar medalhas: {e}")
    
    def print_summary(self) -> None:
        """Exibe resumo dos diretórios e arquivos."""
        logger.info("\n" + "="*60)
        logger.info("IMPORTADOR DE MEDALHAS - Resumo de Configuração")
        logger.info("="*60)
        logger.info(f"Diretório do projeto: {self.project_root}")
        logger.info(f"Diretório de descrições: {self.descriptions_dir}")
        logger.info(f"Diretório de imagens: {self.images_dir}")
        logger.info(f"Diretório de ribbons: {self.ribbons_dir}")
        logger.info(f"Arquivo de saída: {self.output_file}")
        logger.info("="*60 + "\n")


def main():
    """Função principal de execução."""
    importer = MedalDescriptionImporter()
    importer.print_summary()
    
    # Importa medalhas
    medals = importer.import_all()
    
    if medals:
        importer.save_to_file(medals)
        logger.info("\n✓ Importação concluída com sucesso!\n")
    else:
        logger.warning("\n⚠ Nenhuma medalha foi importada.\n")


if __name__ == "__main__":
    main()
