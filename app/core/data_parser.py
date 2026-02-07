# ===================================================================
# IL2 Campaign Analyzer - data_parser.py
# Parser de dados brutos de campanhas PWCGFC com cache e validação robusta
# ===================================================================

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple, Set
from functools import lru_cache

logger = logging.getLogger("IL2CampaignAnalyzer")


class IL2DataParser:
    """Lê e extrai dados brutos dos arquivos da campanha PWCGFC.
    
    Responsável por acessar e carregar arquivos JSON das campanhas do PWCG,
    incluindo informações de campanha, ases, pessoal de esquadrão, relatórios
    de combate e dados de missões. Implementa cache para otimizar I/O e
    fallback de encoding para arquivos legados.
    
    Attributes:
        pwcgfc_path: Caminho raiz do diretório PWCGFC
        campaigns_path: Caminho do diretório de campanhas
    """
    
    def __init__(self, pwcgfc_path: Union[str, Path, None]) -> None:
        """Inicializa o parser com o caminho do PWCGFC.
        
        Args:
            pwcgfc_path: Caminho do diretório raiz do PWCGFC. Aceita None, string
                ou Path. Se None ou inválido, usa diretório de trabalho atual.
        """
        # Normalização robusta do caminho
        if isinstance(pwcgfc_path, Path):
            self.pwcgfc_path: Path = pwcgfc_path
        else:
            try:
                self.pwcgfc_path: Path = Path(pwcgfc_path) if pwcgfc_path else Path.cwd()
            except (TypeError, ValueError):
                # TypeError se pwcgfc_path não for str/PathLike
                # ValueError se for string inválida como caminho
                logger.warning(
                    f"Caminho PWCGFC inválido: {pwcgfc_path}. "
                    "Usando diretório de trabalho atual."
                )
                self.pwcgfc_path: Path = Path.cwd()
        
        self.campaigns_path: Path = self.pwcgfc_path / 'User' / 'Campaigns'
        logger.info(f"Parser inicializado com caminho: {self.pwcgfc_path}")
    
    @lru_cache(maxsize=128)
    def _get_json_data_cached(self, file_path_str: str) -> Optional[Any]:
        """Versão cacheada de carregamento de JSON.
        
        Args:
            file_path_str: String do caminho do arquivo (para compatibilidade com lru_cache)
            
        Returns:
            Dados JSON parseados ou None se houver erro
        """
        return self._load_json_file(Path(file_path_str))
    
    def get_json_data(self, file_path: Path) -> Optional[Any]:
        """Carrega JSON de arquivo com cache LRU e fallback de encoding.
        
        Tenta múltiplos encodings em ordem (UTF-8, Latin-1, UTF-8 tolerante)
        para maximizar compatibilidade com arquivos legados.
        
        Args:
            file_path: Caminho do arquivo JSON
            
        Returns:
            Dados JSON parseados ou None se houver erro
        """
        try:
            file_path_resolved = file_path.resolve()
            return self._get_json_data_cached(str(file_path_resolved))
        except (TypeError, ValueError, OSError) as e:
            # OSError para symlinks quebrados, TypeError/ValueError para paths inválidos
            logger.warning(f"Não foi possível resolver caminho {file_path}: {e}")
            return self._load_json_file(file_path)
    
    def _load_json_file(self, file_path: Path) -> Optional[Any]:
        """Carrega arquivo JSON com fallback de encoding.
        
        Args:
            file_path: Caminho do arquivo JSON
            
        Returns:
            Dados JSON parseados ou None se houver erro
        """
        if not file_path.exists():
            logger.debug(f"Arquivo não encontrado: {file_path}")
            return None
        
        # Tentativa 1: UTF-8 (padrão moderno)
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"JSON carregado com UTF-8: {file_path.name}")
            return data
        except json.JSONDecodeError as e:
            logger.debug(
                f"Falha UTF-8 em {file_path.name} (pos {e.pos}), "
                "tentando Latin-1..."
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"Erro ao abrir {file_path}: {e}")
            return None
        
        # Tentativa 2: Latin-1 (arquivos legados Windows)
        try:
            with file_path.open('r', encoding='latin-1') as f:
                data = json.load(f)
            logger.info(f"JSON carregado com Latin-1: {file_path.name}")
            return data
        except json.JSONDecodeError:
            logger.debug(f"Falha Latin-1 em {file_path.name}, tentando modo tolerante...")
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"Erro ao ler {file_path} (Latin-1): {e}")
            return None
        
        # Tentativa 3: UTF-8 tolerante (substitui caracteres inválidos)
        try:
            text = file_path.read_text(encoding='utf-8', errors='replace')
            data = json.loads(text)
            logger.warning(
                f"JSON carregado com substituição de caracteres: {file_path.name}"
            )
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Falha final ao decodificar {file_path}: {e}")
            return None
    
    def get_campaigns(self) -> List[str]:
        """Lista todas as campanhas disponíveis.
        
        Returns:
            Lista ordenada de nomes de campanhas (diretórios)
        """
        if not self.campaigns_path.exists():
            logger.warning(f"Pasta de campanhas não encontrada: {self.campaigns_path}")
            return []
        
        try:
            campaigns = [
                p.name 
                for p in self.campaigns_path.iterdir() 
                if p.is_dir()
            ]
            logger.info(f"Encontradas {len(campaigns)} campanhas")
            return sorted(campaigns)
        except OSError as e:
            # Captura PermissionError, FileNotFoundError e outros erros de I/O
            logger.error(f"Erro ao listar campanhas em {self.campaigns_path}: {e}")
            return []
    
    def get_campaign_info(self, campaign_name: str) -> Dict[str, Any]:
        """Carrega informações básicas da campanha.
        
        Args:
            campaign_name: Nome da campanha
            
        Returns:
            Dicionário com dados da campanha ou vazio se não encontrado
        """
        path = self.campaigns_path / campaign_name / 'Campaign.json'
        data = self.get_json_data(path)
        if data:
            logger.debug(f"Info da campanha '{campaign_name}' carregada")
        return data or {}
    
    def get_campaign_aces(self, campaign_name: str) -> List[Dict[str, Any]]:
        """Carrega os ases da campanha.
        
        Suporta múltiplos formatos de arquivo PWCG:
        - Lista direta de ases
        - Dict com chave 'aces'
        - Dict com chave 'acesInCampaign' (formato PWCG recente)
        
        Args:
            campaign_name: Nome da campanha
            
        Returns:
            Lista de dicionários com dados dos ases
        """
        aces_path = self.campaigns_path / campaign_name / 'CampaignAces.json'
        data = self.get_json_data(aces_path)
        
        if not data:
            logger.debug(f"Nenhum ás encontrado para campanha '{campaign_name}'")
            return []
        
        # Formato: lista direta
        if isinstance(data, list):
            logger.debug(f"Carregados {len(data)} ases (formato lista)")
            return data
        
        # Formato: dict com chave 'aces'
        if isinstance(data, dict):
            if "aces" in data and isinstance(data["aces"], list):
                logger.debug(f"Carregados {len(data['aces'])} ases (chave 'aces')")
                return data["aces"]
            
            # Formato: dict com chave 'acesInCampaign'
            if "acesInCampaign" in data and isinstance(data["acesInCampaign"], dict):
                aces_list = list(data["acesInCampaign"].values())
                logger.debug(
                    f"Carregados {len(aces_list)} ases (chave 'acesInCampaign')"
                )
                return aces_list
        
        logger.warning(f"Formato de ases não reconhecido em '{campaign_name}'")
        return []
    
    def get_squadron_personnel(
        self, 
        campaign_name: str, 
        squadron_id: int
    ) -> Dict[str, Any]:
        """Carrega o pessoal de um esquadrão específico.
        
        Args:
            campaign_name: Nome da campanha
            squadron_id: ID numérico do esquadrão
            
        Returns:
            Dicionário com dados do pessoal ou vazio se não encontrado
        """
        personnel_path = (
            self.campaigns_path / campaign_name / 'Personnel' / f'{squadron_id}.json'
        )
        data = self.get_json_data(personnel_path)
        if data:
            logger.debug(f"Pessoal do esquadrão {squadron_id} carregado")
        return data or {}
    
    def get_combat_reports(
        self, 
        campaign_name: str, 
        player_serial: str
    ) -> List[Dict[str, Any]]:
        """Carrega relatórios de combate de um piloto, ordenados por data (mais recente primeiro).
        
        Args:
            campaign_name: Nome da campanha
            player_serial: Serial numérico do piloto
            
        Returns:
            Lista de dicionários com relatórios de combate
        """
        reports_path = (
            self.campaigns_path / campaign_name / 'CombatReports' / player_serial
        )
        
        if not reports_path.exists() or not reports_path.is_dir():
            logger.debug(
                f"Pasta de relatórios não encontrada para serial {player_serial}: "
                f"{reports_path}"
            )
            return []
        
        # Coleta arquivos com timestamp para ordenação
        files: List[Tuple[float, Path]] = []
        for report_file in reports_path.glob('*.json'):
            try:
                mtime = report_file.stat().st_mtime
            except OSError:
                # Arquivo pode ter sido deletado entre glob() e stat()
                logger.warning(f"Não foi possível acessar {report_file.name}")
                mtime = 0
            files.append((mtime, report_file))
        
        # Ordena por data de modificação (mais recente primeiro)
        files.sort(key=lambda x: x[0], reverse=True)
        
        # Carrega relatórios
        reports: List[Dict[str, Any]] = []
        for _, report_file in files:
            report_data = self.get_json_data(report_file)
            if isinstance(report_data, dict):
                reports.append(report_data)
            else:
                logger.warning(
                    f"Dados de relatório inválidos em {report_file.name}: "
                    f"{type(report_data)}"
                )
        
        logger.info(f"Carregados {len(reports)} relatórios para serial {player_serial}")
        return reports
    
    def get_mission_data(
        self, 
        campaign_name: str, 
        report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Busca dados completos de uma missão a partir do relatório de combate.
        
        Realiza busca heurística por arquivos de missão baseada em:
        1. Data + nome do piloto
        2. Nome do piloto (se data falhar)
        3. Data apenas
        4. Regex de data
        
        Args:
            campaign_name: Nome da campanha PWCG
            report: Dicionário com dados do relatório de combate contendo
                'reportPilotName', 'date', etc
        
        Returns:
            Dicionário com dados completos da missão incluindo descrição,
            aviões participantes e condições meteorológicas. Retorna dict
            vazio se a missão não for encontrada.
        
        Example:
            >>> report = {'reportPilotName': 'Lt. Hans Schmidt', 'date': '19180515'}
            >>> data = parser.get_mission_data('Campaign1', report)
            >>> print(data.get('missionDescription', 'N/A'))
        """
        mission_data_dir: Path = self.campaigns_path / campaign_name / 'MissionData'
        
        if not mission_data_dir.exists() or not mission_data_dir.is_dir():
            logger.warning(f"Diretório MissionData não encontrado: {mission_data_dir}")
            return {}
        
        # Extrai e limpa nome do piloto
        pilot_name: str = (report.get("reportPilotName") or "") or ""
        pilot_name_clean: str = self._clean_pilot_name(pilot_name)
        
        # Valida e formata data
        date_str_yyyymmdd: str = report.get("date", "") or ""
        if not self._is_valid_date_string(date_str_yyyymmdd):
            logger.warning(
                f"Data da missão ausente ou inválida no relatório: {date_str_yyyymmdd}"
            )
            return {}
        
        try:
            date_obj: datetime = datetime.strptime(date_str_yyyymmdd, '%Y%m%d')
            date_str_dashed: str = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error(f"Formato de data inválido: {date_str_yyyymmdd}")
            return {}
        
        # Coleta candidatos de arquivos
        candidates: List[Path] = self._collect_mission_file_candidates(mission_data_dir)
        if not candidates:
            logger.warning(f"Nenhum arquivo de missão encontrado em {mission_data_dir}")
            return {}
        
        # Busca heurística
        match_candidates: List[Path] = self._find_mission_file_matches(
            candidates, 
            pilot_name_clean, 
            date_str_dashed
        )
        
        if not match_candidates:
            logger.warning(
                f"Nenhum arquivo de missão correspondente para piloto '{pilot_name_clean}' "
                f"na data '{date_str_dashed}'"
            )
            return {}
        
        # Ordena por data de modificação (mais recente primeiro)
        try:
            match_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        except OSError:
            # Falha ao obter stat() de algum arquivo
            logger.debug("Falha ao ordenar candidatos por timestamp")
        
        # Tenta carregar o primeiro candidato válido
        for candidate in match_candidates:
            data: Optional[Any] = self.get_json_data(candidate)
            if isinstance(data, dict):
                logger.info(f"Arquivo de missão encontrado: {candidate.name}")
                return data
            else:
                logger.debug(f"Candidato inválido: {candidate.name} -> {type(data)}")
        
        logger.warning(
            f"Nenhum arquivo válido de missão para '{pilot_name_clean}' "
            f"em '{date_str_dashed}'"
        )
        return {}
    
    @staticmethod
    def _clean_pilot_name(pilot_name: str) -> str:
        """Remove patentes e normaliza nome do piloto.
        
        Args:
            pilot_name: Nome completo do piloto com patente
            
        Returns:
            Nome limpo (sem patente, espaços normalizados)
        """
        # Remove patentes comuns
        cleaned: str = re.sub(
            r'^(?:Lieutenant|Ltn|Fw|Obltn|Cne|S/Lt|Sergt|Lt|Capt|Major|Maj)\\.?\\s*',
            '',
            pilot_name,
            flags=re.IGNORECASE
        ).strip()
        
        # Normaliza espaços
        cleaned = re.sub(r'\\s+', ' ', cleaned).strip()
        return cleaned
    
    @staticmethod
    def _is_valid_date_string(date_str: str) -> bool:
        """Valida formato de data YYYYMMDD.
        
        Args:
            date_str: String de data a validar
            
        Returns:
            True se formato válido, False caso contrário
        """
        return (
            bool(date_str) and 
            len(date_str) == 8 and 
            date_str.isdigit()
        )
    
    def _collect_mission_file_candidates(
        self, 
        mission_data_dir: Path
    ) -> List[Path]:
        """Coleta todos os arquivos de missão candidatos, removendo duplicatas.
        
        Args:
            mission_data_dir: Diretório de MissionData
            
        Returns:
            Lista de Paths únicos de arquivos candidatos
        """
        candidates: List[Path] = []
        
        try:
            # Padrões de busca em ordem de especificidade
            candidates += list(mission_data_dir.glob('*MissionData.json'))
            candidates += list(mission_data_dir.glob('*.MissionData.json'))
            candidates += list(mission_data_dir.glob('*.json'))
            
            # Remove duplicatas preservando ordem
            seen: Set[str] = set()
            unique: List[Path] = []
            
            for p in candidates:
                try:
                    resolved = str(p.resolve())
                except OSError:
                    # Symlink quebrado ou permissão negada
                    resolved = str(p)
                
                if resolved not in seen:
                    seen.add(resolved)
                    unique.append(p)
            
            logger.debug(f"Coletados {len(unique)} arquivos candidatos de missão")
            return unique
            
        except OSError as e:
            logger.warning(f"Erro ao listar arquivos de MissionData: {e}")
            return []
    
    def _find_mission_file_matches(
        self, 
        candidates: List[Path], 
        pilot_name_clean: str, 
        date_str_dashed: str
    ) -> List[Path]:
        """Busca heurística por arquivos de missão correspondentes.
        
        Implementa busca em 4 níveis de especificidade:
        1. Data + nome do piloto (match exato)
        2. Nome do piloto apenas
        3. Data apenas
        4. Regex de data (fallback)
        
        Args:
            candidates: Lista de arquivos candidatos
            pilot_name_clean: Nome do piloto (sem patente)
            date_str_dashed: Data no formato YYYY-MM-DD
            
        Returns:
            Lista de Paths correspondentes (ordenada por relevância)
        """
        lower_pilot: str = pilot_name_clean.lower()
        lower_date: str = date_str_dashed.lower()
        
        # Nível 1: Data + nome do piloto
        match_candidates: List[Path] = [
            f for f in candidates
            if lower_date in f.name.lower() and (
                not lower_pilot or lower_pilot in f.name.lower()
            )
        ]
        
        if match_candidates:
            logger.debug(f"Encontrados {len(match_candidates)} matches (data+piloto)")
            return match_candidates
        
        # Nível 2: Nome do piloto apenas
        if lower_pilot:
            match_candidates = [
                f for f in candidates
                if lower_pilot in f.name.lower()
            ]
            if match_candidates:
                logger.debug(f"Encontrados {len(match_candidates)} matches (piloto)")
                return match_candidates
        
        # Nível 3: Data apenas
        match_candidates = [
            f for f in candidates
            if lower_date in f.name.lower()
        ]
        
        if match_candidates:
            logger.debug(f"Encontrados {len(match_candidates)} matches (data)")
            return match_candidates
        
        # Nível 4: Regex de data (fallback)
        date_regex: re.Pattern = re.compile(r'\\d{4}-\\d{2}-\\d{2}')
        nearest: List[Path] = [
            f for f in candidates
            if (m := date_regex.search(f.name)) and m.group(0) == date_str_dashed
        ]
        
        if nearest:
            logger.debug(f"Encontrados {len(nearest)} matches (regex)")
            return nearest
        
        return []
