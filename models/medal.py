# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - models/medal.py
# Modelos de dados para medalhas com validação Pydantic
# ===================================================================

from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Optional

class MedalCondition(BaseModel):
    """Representa uma condição para conquista de medalha.
    
    Attributes:
        descricao: Descrição textual da condição
        tipo: Tipo/categoria da condição
        valor: Valor numérico ou textual da condição
    """
    descricao: str = Field(..., min_length=1, description="Descrição da condição")
    tipo: str = Field(..., min_length=1, description="Tipo da condição")
    valor: str = Field(default="", description="Valor da condição")


class Medal(BaseModel):
    """Representa uma medalha/condecoração militar.
    
    Attributes:
        nome: Nome oficial da medalha
        imagem_path: Caminho relativo da imagem da medalha
        ribbon_path: Caminho relativo da ribbon (opcional)
        country: Código do país de origem
        descricao: Descrição histórica/explicativa
        condicoes: Lista de condições para conquista
    """
    nome: str = Field(..., min_length=1, description="Nome da medalha")
    imagem_path: str = Field(..., min_length=1, description="Caminho da imagem")
    ribbon_path: Optional[str] = Field(default=None, description="Caminho da ribbon")
    country: str = Field(default='germany', description="País de origem")
    descricao: str = Field(default='', description="Descrição da medalha")
    condicoes: List[MedalCondition] = Field(
        default_factory=list, 
        description="Lista de condições para conquista"
    )
    
    @field_validator('country')
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Valida código do país.
        
        Args:
            v: Código do país a validar
            
        Returns:
            Código do país normalizado (lowercase)
            
        Raises:
            ValueError: Se país não for válido
        """
        valid_countries = ['germany', 'france', 'britain', 'usa', 'belgian']
        normalized = v.lower().strip()
        
        if normalized not in valid_countries:
            raise ValueError(
                f"País inválido: '{v}'. Países válidos: {', '.join(valid_countries)}"
            )
        
        return normalized
    
    @field_validator('condicoes')
    @classmethod
    def validate_condicoes(cls, v: List[MedalCondition]) -> List[MedalCondition]:
        """Valida lista de condições.
        
        Args:
            v: Lista de condições a validar
            
        Returns:
            Lista de condições validada
            
        Raises:
            ValueError: Se lista estiver vazia
        """
        if not v:
            raise ValueError("A medalha deve ter pelo menos uma condição")
        
        return v


# Exemplo de uso (para referência)
if __name__ == "__main__":
    # Exemplo válido
    try:
        medal = Medal(
            nome="Pour le Mérite",
            imagem_path="images/pour_le_merite.png",
            ribbon_path="ribbons/pour_le_merite.png",
            country="germany",
            descricao="Medalha de honra militar prussiana",
            condicoes=[
                MedalCondition(
                    descricao="Abater 8 aviões inimigos",
                    tipo="victories",
                    valor="8"
                )
            ]
        )
        print("Medalha válida:", medal.nome)
        print("País:", medal.country)
        print("Condições:", len(medal.condicoes))
    except ValidationError as e:
        print("Erro de validação:", e)
    
    # Exemplo inválido (país)
    try:
        invalid_medal = Medal(
            nome="Test Medal",
            imagem_path="test.png",
            country="invalid_country",
            condicoes=[
                MedalCondition(descricao="Test", tipo="test", valor="1")
            ]
        )
    except ValidationError as e:
        print("\nErro esperado (país inválido):")
        print(e)
    
    # Exemplo inválido (sem condições)
    try:
        invalid_medal2 = Medal(
            nome="Test Medal",
            imagem_path="test.png",
            country="germany",
            condicoes=[]
        )
    except ValidationError as e:
        print("\nErro esperado (sem condições):")
        print(e)
