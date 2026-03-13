"""
Gemini integration — function calling para consultas em linguagem natural.

Fluxo:
  1. Usuário envia mensagem
  2. Enviamos ao Gemini com definições das tools (mapeadas nos endpoints)
  3. Gemini decide qual function chamar (ou responde direto)
  4. Executamos a query correspondente no PostgreSQL
  5. Re-enviamos resultado ao Gemini para formatação em linguagem natural
  6. Retornamos resposta ao usuário
"""

import os
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

import queries
from schemas import ChatResponse


# ---------------------------------------------------------------------------
# Definição das tools para o Gemini
# ---------------------------------------------------------------------------

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="list_areas",
                description="Lista todas as áreas de avaliação disponíveis no sistema QUALIS.",
                parameters=types.Schema(type=types.Type.OBJECT, properties={}),
            ),
            types.FunctionDeclaration(
                name="search_periodicos",
                description=(
                    "Busca periódicos científicos com filtros opcionais. "
                    "Use esta função quando o usuário quiser encontrar periódicos "
                    "por área, estrato (classificação) ou título/ISSN."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "area": types.Schema(
                            type=types.Type.STRING,
                            description="Área de avaliação exata conforme retornada por list_areas.",
                        ),
                        "estrato": types.Schema(
                            type=types.Type.STRING,
                            description="Classificação QUALIS: A1, A2, A3, A4, B1, B2, B3, B4 ou C.",
                            enum=["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "C"],
                        ),
                        "search": types.Schema(
                            type=types.Type.STRING,
                            description="Texto para buscar no título ou ISSN do periódico.",
                        ),
                        "page": types.Schema(
                            type=types.Type.INTEGER,
                            description="Número da página (padrão: 1).",
                        ),
                        "per_page": types.Schema(
                            type=types.Type.INTEGER,
                            description="Resultados por página (padrão: 10, máx: 50).",
                        ),
                    },
                ),
            ),
            types.FunctionDeclaration(
                name="get_distribuicao",
                description=(
                    "Retorna a distribuição de classificações (estratos) para uma área, "
                    "com contagem e percentual de cada estrato. "
                    "Use quando o usuário quiser saber como os periódicos de uma área "
                    "estão distribuídos entre A1, A2, B1, etc."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "area": types.Schema(
                            type=types.Type.STRING,
                            description="Área de avaliação exata conforme retornada por list_areas.",
                        ),
                    },
                    required=["area"],
                ),
            ),
        ]
    )
]

SYSTEM_INSTRUCTION = """
Você é um assistente especializado no sistema QUALIS CAPES, que classifica periódicos científicos
no Brasil. Ajude coordenadores de pós-graduação a consultar as classificações.

Regras:
- Responda sempre em português do Brasil
- Use as funções disponíveis para consultar dados reais do banco
- Apresente resultados de forma clara e objetiva
- Se o usuário perguntar sobre uma área específica, use exatamente o nome da área como retornado por list_areas
- Quando listar periódicos, mostre título, ISSN e estrato de forma organizada
- Estratos de A1 (mais alto) a C (mais baixo)
"""


# ---------------------------------------------------------------------------
# Execução das function calls
# ---------------------------------------------------------------------------

def _execute_function(name: str, args: dict, db: Session) -> Any:
    """Despacha a function call do Gemini para a query correspondente."""
    if name == "list_areas":
        return queries.get_areas(db)

    elif name == "search_periodicos":
        items, total = queries.search_periodicos(
            db,
            area=args.get("area"),
            estrato=args.get("estrato"),
            search=args.get("search"),
            page=args.get("page", 1),
            per_page=min(args.get("per_page", 10), 50),  # cap de segurança
        )
        return {"items": items, "total": total}

    elif name == "get_distribuicao":
        return queries.get_distribuicao(db, area=args["area"])

    raise ValueError(f"Função desconhecida: {name}")


# ---------------------------------------------------------------------------
# Handler principal
# ---------------------------------------------------------------------------

async def handle_chat(message: str, db: Session) -> ChatResponse:
    """
    Processa uma mensagem de linguagem natural usando Gemini function calling.
    Retorna resposta formatada + dados brutos quando aplicável.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=api_key)

    contents = [types.Content(role="user", parts=[types.Part(text=message)])]

    # --- Turno 1: Gemini decide qual function chamar ---
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=TOOLS,
            temperature=0.2,
        ),
    )

    candidate = response.candidates[0]
    action_taken = None
    raw_data = None

    # Verifica se o Gemini quer chamar uma função
    function_calls = [
        part.function_call
        for part in candidate.content.parts
        if part.function_call is not None
    ]

    if function_calls:
        fc = function_calls[0]
        action_taken = fc.name
        func_args = dict(fc.args) if fc.args else {}

        # Executa a query
        result = _execute_function(fc.name, func_args, db)
        raw_data = result if isinstance(result, list) else (
            result.get("items") if isinstance(result, dict) else None
        )

        # --- Turno 2: Re-envia resultado para o Gemini formatar ---
        contents.append(candidate.content)
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": result},
                        )
                    )
                ],
            )
        )

        final_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOLS,
                temperature=0.2,
            ),
        )
        text_response = final_response.text or "Não foi possível formatar a resposta."
    else:
        # Gemini respondeu diretamente (sem function call)
        text_response = response.text or "Não entendi sua pergunta. Tente reformular."

    return ChatResponse(
        response=text_response,
        data=raw_data,
        action_taken=action_taken,
    )
