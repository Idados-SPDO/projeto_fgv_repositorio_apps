# 🎯 Plano de Organização — Gestão de Dados (SPDO)

> Transição iniciada em **25/06/2026** | Responsável anterior retorna em **13/07/2026**  
> Reporte na ausência: **Flavio** ou **Arnaldo**

---

## 1. Mapa das Responsabilidades

Suas atividades se dividem em **4 categorias operacionais** + **1 categoria de desenvolvimento**:

| # | Categoria | Tipo | Frequência | Criticidade |
|---|-----------|------|------------|-------------|
| 1 | **Dados de Parceria** | Operacional | Conforme periodicidade do parceiro | 🔴 Alta |
| 2 | **Tabelas de Coleta** | Operacional | Conforme demanda do pesquisador | 🔴 Alta |
| 3 | **Dados Externos** | Operacional | Conforme periodicidade da fonte | 🟡 Média |
| 4 | **Consultas ao Banco de Preços** | Operacional/Sob demanda | Conforme solicitação | 🟡 Média |
| 5 | **DataCore + Projetos Secundários** | Desenvolvimento | Planejado | 🟢 Estratégico |

---

## 2. Princípio Central: Operação Primeiro, Projetos Depois

> ⚠️ **IMPORTANTE**: A regra de ouro é: **a operação não pode parar**. Projetos são importantes, mas a continuidade dos processos existentes é a sua prioridade #1 durante a transição.

### Matriz de Priorização Diária

```
┌──────────────────────────────────────────────────────┐
│  PRIORIDADE 1 (Faça IMEDIATAMENTE)                   │
│  → Falhas em ingestão / dados não recebidos          │
│  → Demandas do Flavio/Arnaldo                        │
│  → Problemas em ambientes Snowflake                  │
├──────────────────────────────────────────────────────┤
│  PRIORIDADE 2 (Faça NO MESMO DIA)                    │
│  → Monitoramento de recebimento de dados             │
│  → Novas demandas de consulta ao banco               │
│  → Responder parceiros / pesquisadores               │
├──────────────────────────────────────────────────────┤
│  PRIORIDADE 3 (Planeje na SEMANA)                    │
│  → Novas ingestões e transformações                  │
│  → Documentação de bases                             │
│  → Acompanhamento de demandas TI-IBRE                │
├──────────────────────────────────────────────────────┤
│  PRIORIDADE 4 (Blocos DEDICADOS)                     │
│  → DataCore                                          │
│  → Projetos secundários                              │
│  → Melhorias de processo                             │
└──────────────────────────────────────────────────────┘
```

---

## 3. Rotina Semanal Sugerida

### Bloco Diário Fixo (todos os dias, ~30-45 min pela manhã)

- [ ] **Checklist de Monitoramento** — verificar se todos os dados esperados chegaram
- [ ] **Verificar e-mails/mensagens** — filtrar por demandas urgentes
- [ ] **Atualizar planilha de controle** — registrar status de cada atividade

### Distribuição Semanal

| Dia | Manhã (Operação) | Tarde (Flexível) |
|-----|-------------------|-------------------|
| **Segunda** | Monitoramento + triagem da semana | Planejamento semanal + demandas novas |
| **Terça** | Operação (ingestões, transformações) | 🟦 **Bloco DataCore** |
| **Quarta** | Operação + consultas ao banco | Documentação de bases |
| **Quinta** | Operação (ingestões, transformações) | 🟦 **Bloco DataCore / Projetos** |
| **Sexta** | Monitoramento + fechamento semanal | Retrospectiva + preparação próxima semana |

> 💡 **DICA**: Reserve as **tardes de terça e quinta** como blocos protegidos para projetos. Se surgir uma urgência operacional, use esse tempo, mas **reponha** na próxima oportunidade. A chave é ter horários fixos para projetos, senão a operação consome 100% do tempo.

---

## 4. Sistema de Controle — Planilhas

As planilhas de controle estão na pasta `docs/planilhas/`:

- **painel_monitoramento_dados.csv** — Controle de recebimento de todas as fontes de dados
- **backlog_demandas.csv** — Registro e acompanhamento de todas as demandas
- **registro_documentacao.csv** — Controle do status de documentação de cada base

---

## 5. Checklists por Tipo de Atividade

### 📦 Dados de Parceria — Novo Parceiro

```
□ Participar da agenda de entendimento dos dados
□ Definir modelo de envio/recebimento (formato, canal)
□ Levantar informações para solicitação de ambiente:
    □ Tipo de dado a ser compartilhado
    □ Possui dado sensível?
    □ Formato do dado (CSV, JSON, etc.)
    □ Volumetria estimada e periodicidade
    □ Volume dos arquivos
□ Solicitar provisão de ambiente à TI-IBRE (SFTP ou AWS)
    → Contato: Victor (alinhamento) + Rafaella Bezerra (abertura de demanda)
□ Solicitar ingestão automática para Snowflake
□ Configurar monitoramento de recebimento
□ Realizar transformações na Snowflake (BASES_SPDO)
□ Disponibilizar carga para Banco de Preços (se solicitado → Flavio)
□ Criar documentação da base
```

### 📊 Tabelas de Coleta — Nova Tabela

```
□ Receber demanda do pesquisador responsável
□ Combinar local de armazenamento (pasta)
□ Realizar entendimento (dados, formato)
□ Ingerir na Snowflake → BASES_SPDO (dado RAW/bruto)
□ Agendar processo de ingestão incremental
□ Criar transformação bruto → formato de carga
□ Configurar monitoramento de recebimento
□ Monitorar antes de enviar carga → Gestão do Banco de Preços
□ Criar documentação
⚠️ Em caso de falta no envio: CONVERSAR COM O FLAVIO antes de agir
```

### 🌐 Dados Externos — Nova Fonte

```
□ Realizar entendimento dos dados
□ Solicitar ingestão AWS → Snowflake
□ Configurar monitoramento (periodicidade da fonte)
□ Criar documentação
```

### 🔍 Consultas ao Banco de Preços

```
□ Receber solicitação
□ Entender requisitos + definir prazo e periodicidade com solicitante
□ Desenvolver consulta na Snowflake
□ Agendar conforme periodicidade
□ Automatizar envio para área usuária
```

---

## 6. Informações de Referência Rápida

### Ambiente Snowflake

| Item | Valor |
|------|-------|
| **Workspace** | `GESTAO_DADOS` |
| **Schema - Dados Externos** | `DB_GESTAO_DADOS_EXTERNOS` |
| **Schema - Banco de Preços** | `DB_GESTAO_BANCO_PRECO` |

> ⚠️ **ATENÇÃO**: Respeitar padrões de nomenclatura ao criar tabelas, schemas, procedures, etc. Verificar exemplos existentes antes de criar novos objetos.

### Contatos-Chave

| Pessoa | Papel | Quando Acionar |
|--------|-------|----------------|
| **Flavio** | Reporte / Gestão Banco de Preços | Dúvidas operacionais, cargas, falta de dados |
| **Arnaldo** | Reporte alternativo | Na ausência do Flavio |
| **Victor** | TI-IBRE | Andamento de demandas técnicas (ex: SDIBRE-1149) |
| **Rafaella Bezerra** | TI-IBRE | Abertura de novas demandas |
| **Olivio** | Equipe (apoiando Flavio) | Governança, cadastro, Banco de Preços |
| **Brendon** | Equipe | Atividades operacionais |

### Parcerias Ativas

| Parceiro | Status | Observações |
|----------|--------|-------------|
| **Neogrid/Horus** | Ativo | — |
| **Pastorinho** | Ativo | — |
| **Starian** | Ativo | — |

### Demandas Pendentes TI-IBRE

| Ticket | Descrição | Ação |
|--------|-----------|------|
| **SDIBRE-1149** | Verificar andamento | Falar com **Victor** |

---

## 7. Estratégia para Projetos Secundários + DataCore

> ⚠️ **IMPORTANTE**: Não tente fazer tudo ao mesmo tempo. Nas primeiras 2-3 semanas, foque 80% na operação e 20% em projetos. Conforme você dominar as rotinas, essa proporção pode ir para 60/40.

### Fase 1: Transição (Semanas 1-2) — até ~09/07

- **Foco**: Entender todos os processos, mapear o que está rodando, onde estão os dados
- **Projetos**: Apenas leitura/entendimento do estado atual do DataCore
- **Meta**: Conseguir executar o monitoramento diário de forma autônoma

### Fase 2: Estabilização (Semanas 3-4) — até ~23/07

- **Foco**: Operar com autonomia, resolver demandas sem precisar consultar terceiros
- **Projetos**: Começar pequenas entregas no DataCore (1-2 features por semana)
- **Meta**: Ter a planilha de controle completa e atualizada

### Fase 3: Velocidade de Cruzeiro (Semana 5+)

- **Foco**: Operação rotineira + dedicação crescente a projetos
- **Projetos**: Sprints semanais no DataCore + projetos secundários
- **Meta**: Equilíbrio sustentável entre operação e desenvolvimento

---

## 8. Dicas Práticas

### ✅ Faça

- **Documente tudo** desde o dia 1 — você vai agradecer a si mesmo depois
- **Pergunte ao Brendon e Olivio** nas primeiras semanas — eles conhecem os processos
- **Crie alertas automáticos** na Snowflake para monitorar falhas de ingestão
- **Mantenha um log diário** breve (3 linhas: o que fez, o que está pendente, bloqueios)
- **Comunique proativamente** ao Flavio/Arnaldo sobre qualquer risco

### ❌ Evite

- Tentar absorver tudo de uma vez — priorize a operação
- Aceitar todas as demandas com prazo imediato — negocie prazos realistas
- Trabalhar em projetos quando há pendências operacionais críticas
- Ficar sem documentar por mais de uma semana

---

## 9. Template de Log Diário

Use este formato simples no final de cada dia:

```
📅 Data: dd/mm/aaaa

✅ Feito hoje:
- [atividade 1]
- [atividade 2]

⏳ Pendente:
- [atividade pendente + prazo]

🚧 Bloqueios:
- [bloqueio + quem pode resolver]

📌 Para amanhã:
- [prioridade 1]
- [prioridade 2]
```

---

## 10. Próximos Passos Imediatos (Semana de 25/06)

- [ ] Agendar conversa com **Brendon** para walkthrough dos processos atuais
- [ ] Agendar conversa com **Olivio** antes da transição total para o Flavio
- [ ] Criar/preencher a planilha de controle (Painel de Monitoramento)
- [ ] Verificar status de todas as ingestões ativas na Snowflake
- [ ] Verificar demanda **SDIBRE-1149** com Victor
- [ ] Fazer levantamento do estado atual do **DataCore** (código, deploy, backlog)
- [ ] Mapear todos os agendamentos existentes na Snowflake (tasks/procedures)
- [ ] Definir quais projetos secundários serão priorizados (listar e classificar)
