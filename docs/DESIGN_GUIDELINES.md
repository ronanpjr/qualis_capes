# Design Guidelines — QUALIS CAPES

> Este documento é a referência de design para toda a aplicação. Deve ser consultado antes de criar qualquer componente visual.

---

## 1. Identidade Visual

**Tom:** Institucional, acadêmico, confiável. A ferramenta é para coordenadores de pós-graduação — profissionais que valorizam clareza e eficiência sobre flashiness.

**Referências:** Portais universitários (USP, UNICAMP), Google Scholar, Sucupira/CAPES, bases de dados acadêmicas (Scopus, Web of Science).

**Princípios:**
1. **Dados em primeiro lugar** — a informação é a protagonista, não a interface
2. **Sobriedade profissional** — sem efeitos chamativos, sem dark mode genérico
3. **Hierarquia clara** — o olho deve saber exatamente para onde ir
4. **Identidade acadêmica** — fontes, cores e layout que remetam ao ambiente universitário

---

## 2. Paleta de Cores

Inspirada em portais institucionais brasileiros e materiais da CAPES.

```
┌─────────────────────────────────────────────────────┐
│  PRIMARY (Azul Institucional)                       │
│  --primary-900: #0D1B3E  (textos, headers)          │
│  --primary-700: #1A3A6B  (botões, links ativos)     │
│  --primary-500: #2E5EA1  (hover, destaques)         │
│  --primary-100: #E8EEF6  (backgrounds suaves)       │
│  --primary-50:  #F4F7FB  (background geral)         │
│                                                     │
│  NEUTRAL (Cinzas quentes)                           │
│  --neutral-900: #1F2937  (texto corpo)              │
│  --neutral-700: #374151  (texto secundário)         │
│  --neutral-400: #9CA3AF  (placeholders, bordas)     │
│  --neutral-200: #E5E7EB  (divisórias)               │
│  --neutral-50:  #F9FAFB  (cards)                    │
│  --white:       #FFFFFF  (superfícies)              │
│                                                     │
│  ESTRATO BADGES (semáforo acadêmico)                │
│  --estrato-a1:  #166534 / bg #DCFCE7  (verde)       │
│  --estrato-a2:  #15803D / bg #DCFCE7               │
│  --estrato-a3:  #3B82F6 / bg #DBEAFE  (azul)       │
│  --estrato-a4:  #6366F1 / bg #E0E7FF  (indigo)     │
│  --estrato-b1:  #CA8A04 / bg #FEF9C3  (amarelo)    │
│  --estrato-b2:  #D97706 / bg #FEF3C7  (âmbar)      │
│  --estrato-b3:  #EA580C / bg #FFEDD5  (laranja)     │
│  --estrato-b4:  #DC2626 / bg #FEE2E2  (vermelho)   │
│  --estrato-c:   #6B7280 / bg #F3F4F6  (cinza)      │
│                                                     │
│  ACCENT                                             │
│  --accent:      #059669  (sucesso, ações positivas) │
│  --danger:      #DC2626  (erros)                    │
│  --warning:     #D97706  (alertas)                  │
└─────────────────────────────────────────────────────┘
```

---

## 3. Tipografia

**Combinação académica:** Serif para identidade + Sans-serif para dados.

| Uso | Fonte | Peso | Tamanho |
|---|---|---|---|
| Logo/Marca | **Merriweather** (serif) | 700 | 24px |
| Títulos h1 | **Merriweather** (serif) | 700 | 28px |
| Títulos h2 | **Inter** (sans-serif) | 600 | 20px |
| Títulos h3 | **Inter** | 600 | 16px |
| Corpo | **Inter** | 400 | 14px |
| Dados tabela | **Inter** | 400 | 13px |
| Labels/Captions | **Inter** | 500 | 12px |
| Badges | **Inter** | 600 | 11px |

**Google Fonts import:**
```
Merriweather:wght@400;700
Inter:wght@400;500;600;700
```

---

## 4. Layout

```
┌──────────────────────────────────────────────────┐
│  HEADER (branco, borda inferior, logo à esquerda)│
│  Logo + "QUALIS CAPES" | subtítulo               │
├──────────────────────────────────────────────────┤
│                                                  │
│  ÁREA DE SELEÇÃO                                 │
│  [Dropdown ou campo pesquisável com as 50 áreas] │
│                                                  │
├──────────────────────────────────────────────────┤
│  PAINEL DE CONTEÚDO (aparece após selecionar)    │
│                                                  │
│  ┌─────────────┐  ┌──────────────────────────┐   │
│  │ DISTRIBUIÇÃO│  │ FILTROS + BUSCA           │   │
│  │ (sidebar)   │  │ [chips de estrato]        │   │
│  │             │  │ [campo de busca textual]  │   │
│  │ Barras      │  ├──────────────────────────┤   │
│  │ horizontais │  │ TABELA DE RESULTADOS     │   │
│  │ com contag. │  │ ISSN | Título | Estrato  │   │
│  │             │  │ ...                      │   │
│  │             │  │ [paginação]              │   │
│  └─────────────┘  └──────────────────────────┘   │
│                                                  │
└──────────────────────────────────────────────────┘
```

- **Max-width:** 1200px, centralizado
- **Header:** Fixo, branco, shadow sutil (`0 1px 3px rgba(0,0,0,0.08)`)
- **Responsivo:** Em telas < 768px, distribuição fica acima da tabela (stack vertical)

---

## 5. Componentes

### Badges de Estrato
- Pill shape (`border-radius: 12px`)
- Cores do semáforo acadêmico (seção 2)
- Tamanho compacto: `padding: 2px 10px`
- Texto uppercase, `font-weight: 600`, `font-size: 11px`

### Cards
- Background: `--white`
- Border: `1px solid var(--neutral-200)`
- Border-radius: `8px`
- Shadow: `0 1px 3px rgba(0,0,0,0.06)`
- **Sem** glassmorphism ou blur

### Tabela
- Header: background `--primary-50`, texto `--primary-900`, `font-weight: 600`
- Linhas alternadas: `--white` / `--neutral-50`
- Hover: `--primary-100`
- Bordas: apenas horizontais, `--neutral-200`

### Botões
- Primary: bg `--primary-700`, texto branco, `border-radius: 6px`
- Hover: `--primary-500`
- Sem gradientes, sem sombras exageradas

### Inputs/Select
- Border: `1px solid var(--neutral-400)`
- Border-radius: `6px`
- Focus: `border-color: var(--primary-500)`, `box-shadow: 0 0 0 3px var(--primary-100)`

---

## 6. Espaçamento

Base: `4px`. Usar múltiplos: `8px`, `12px`, `16px`, `24px`, `32px`, `48px`.

---

## 7. Anti-padrões (NÃO USAR)

| ❌ Evitar | ✅ Usar em vez disso |
|---|---|
| Dark mode / fundo escuro | Fundo claro institucional |
| Glassmorphism / blur | Cards com bordas sólidas |
| Gradientes chamativos | Cores sólidas e sóbrias |
| Neon / cores vibrantes | Paleta institucional azul |
| Animações excessivas | Transições sutis (200ms) |
| Fontes display/decorativas | Merriweather + Inter |
| Border-radius > 12px | Cantos sutilmente arredondados |
| Sombras pesadas | Sombras mínimas e suaves |
