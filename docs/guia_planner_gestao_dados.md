# 📋 Guia de Reestruturação — Microsoft Planner

> Baseado no board atual e nas novas responsabilidades da área de Gestão de Dados

---

## 1. Diagnóstico do Board Atual

O Planner atual já tem uma boa base. Estes são os buckets existentes:

| Bucket Atual | Conteúdo | Status |
|---|---|---|
| **Backlog - Não Iniciadas** | ETL contratos Setorial, Documentação de Bases (Licitações, Robôs SUEP/SPDO) | Tarefas pausadas/pendentes |
| **Especificação e Catalogação** | 46 tarefas concluídas | Histórico |
| **Cloud Platform** | Reestruturação Snowflake DB_IBRE | 33 concluídas + 1 ativa |
| **Recebimento de Dados** | Dados Imobiliários (Divino Imóveis, Moraes Administração) | Em andamento |
| **Tabelas de Informantes** | Wirex Cable, TDM, Saint-Gobain/Tekbond, Saint-Gobain | Controle de periodicidade |

---

## 2. Estrutura Proposta dos Buckets

A proposta é **manter o que funciona** e **adicionar buckets** para cobrir todas as atividades. Recomendo a seguinte organização (da esquerda para a direita):

### Visão Geral dos Buckets

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  📥 Backlog  │  📦 Dados    │  📊 Tabelas  │  🌐 Dados    │  🔍 Consul-  │  ☁️ Cloud    │  💻 DataCore │  ✅ Conclu-  │
│  & Triagem   │  de Parceria │  de Coleta   │  Externos    │  tas ao BP   │  Platform    │  & Projetos  │  ídas        │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

### Bucket 1: 📥 Backlog & Triagem

**Propósito**: Ponto de entrada de TODAS as novas demandas. Nada começa sem passar aqui primeiro.

> ⚠️ Toda nova demanda entra aqui. Você classifica, prioriza e move para o bucket correto.

**Tarefas do board atual que ficam aqui:**
- ~~Entendimento do ETL dos dados de contratos Setorial~~ → Avaliar se move para "Dados de Parceria" ou "Dados Externos"

**Rótulos (Labels) sugeridos para este bucket:**
- 🔴 `Urgente` — Resolver hoje
- 🟡 `Esta semana` — Resolver na semana
- 🟢 `Planejado` — Pode ser agendado
- 🔵 `Aguardando terceiro` — Depende de alguém

---

### Bucket 2: 📦 Dados de Parceria

**Propósito**: Gerenciar o ciclo completo de dados de parceiros.

**Tarefas a criar:**

| Tarefa | Checklist Sugerido | Rótulo | Atribuído |
|--------|-------------------|--------|-----------|
| **Neogrid/Horus — Monitoramento** | ☐ Verificar recebimento mensal ☐ Validar dados ☐ Confirmar ingestão Snowflake | `Recorrente` | Murilo |
| **Pastorinho — Monitoramento** | ☐ Verificar recebimento ☐ Validar dados ☐ Confirmar ingestão Snowflake | `Recorrente` | Murilo |
| **Starian — Monitoramento** | ☐ Verificar recebimento ☐ Validar dados ☐ Confirmar ingestão Snowflake | `Recorrente` | Murilo |

**Tarefas do board atual que migram para cá:**
- "Dados Imobiliários: Divino Imóveis" (atualmente em Recebimento de Dados)
- "Dados Imobiliários: Moraes Administração" (atualmente em Recebimento de Dados)

**Template de checklist para NOVA parceria:**
```
☐ Participar da agenda de entendimento
☐ Definir modelo de envio/recebimento
☐ Levantar info para ambiente (tipo, sensível, formato, volumetria)
☐ Solicitar ambiente TI-IBRE (Victor + Rafaella)
☐ Solicitar ingestão AWS → Snowflake
☐ Configurar monitoramento
☐ Transformação na Snowflake
☐ Disponibilizar carga (se solicitado → Flavio)
☐ Criar documentação
```

---

### Bucket 3: 📊 Tabelas de Coleta / Informantes

**Propósito**: Controle das tabelas de coleta de pesquisadores e informantes.

> Este bucket absorve o antigo "Tabelas de Informantes"

**Tarefas do board atual que ficam aqui:**
- 2373 - Wirex Cable
- 68229 - TDM
- 103851 - SAINT-GOBAIN/TEKBOND
- 2533 - SAINT-GOBAIN

**Template de checklist para NOVA tabela de coleta:**
```
☐ Receber demanda do pesquisador
☐ Combinar pasta de armazenamento
☐ Entender tabela (dados, formato)
☐ Ingerir na Snowflake (BASES_SPDO - RAW)
☐ Agendar ingestão incremental
☐ Criar transformação bruto → carga
☐ Monitorar recebimento
☐ Validar antes de enviar ao Banco de Preços
☐ Criar documentação
```

> ⚠️ Se houver falta no envio pelo informante: **criar subtarefa "Alinhar com Flavio"**

---

### Bucket 4: 🌐 Dados Externos

**Propósito**: Fontes públicas e governamentais sem relação direta com Banco de Preços.

**Tarefas a criar:**

| Tarefa | Periodicidade | Status |
|--------|---------------|--------|
| **Base de CEP — Monitoramento** | Verificar atualizações | A mapear |
| **Licitações — Monitoramento** | Conforme fonte | A mapear |
| **COFOG — Monitoramento** | Conforme fonte | A mapear |
| **RAIS — Atualização Anual** | Anual | A mapear |
| **CAGED — Atualização Mensal** | Mensal | A mapear |

**Tarefas do board atual que migram para cá:**
- "Entendimento do ETL dos dados de contratos Setorial" (se for dado externo)

**Template de checklist para NOVA fonte externa:**
```
☐ Entender os dados (formato, periodicidade, conteúdo)
☐ Solicitar ingestão AWS → Snowflake
☐ Configurar monitoramento
☐ Criar documentação
```

---

### Bucket 5: 🔍 Consultas ao Banco de Preços

**Propósito**: Solicitações de consulta ao banco de dados.

**Template de checklist para NOVA consulta:**
```
☐ Receber e registrar solicitação
☐ Entender requisitos com solicitante
☐ Definir prazo e periodicidade
☐ Desenvolver consulta na Snowflake
☐ Testar e validar resultados
☐ Agendar execução (se recorrente)
☐ Automatizar envio para área usuária
```

---

### Bucket 6: ☁️ Cloud Platform & TI

**Propósito**: Demandas de infraestrutura, Snowflake e TI-IBRE.

**Tarefas do board atual que ficam aqui:**
- "Reestruturação Snowflake Schemas DB_IBRE"

**Tarefas a criar:**

| Tarefa | Ação | Prioridade |
|--------|------|------------|
| **SDIBRE-1149 — Acompanhamento** | Verificar andamento com Victor | Alta |

---

### Bucket 7: 💻 DataCore & Projetos

**Propósito**: Desenvolvimento de aplicações e projetos secundários.

**Tarefas a criar:**

| Tarefa | Checklist | Prioridade |
|--------|-----------|------------|
| **DataCore — Levantamento estado atual** | ☐ Revisar código ☐ Verificar deploy ☐ Mapear backlog | Alta |
| **DataCore — Próximas features** | (definir após levantamento) | Média |

**Tarefas do board atual que migram para cá:**
- "Documentação de Bases" (Licitações, Robôs SUEP, Robôs SPDO) → se relacionado ao DataCore

---

### Bucket 8: ✅ Concluídas (Semana)

**Propósito**: Mover tarefas concluídas para cá semanalmente. Na sexta-feira, arquive as do bucket.

> 💡 Isso dá visibilidade do que foi entregue na semana — útil para reportar ao Flavio/Arnaldo.

---

## 3. Sistema de Rótulos (Labels)

Configure os rótulos do Planner assim:

| Cor | Rótulo | Uso |
|-----|--------|-----|
| 🟣 Roxo | `Parceria` | Dados de parceiros |
| 🔵 Azul | `Snowflake` | Ações no Snowflake |
| 🟢 Verde | `Dados Externos` | Fontes externas |
| 🟡 Amarelo | `Coleta` | Tabelas de coleta |
| 🟠 Laranja | `Consulta BP` | Consultas ao banco |
| 🔴 Vermelho | `Urgente` | Prioridade máxima |

> Estes rótulos já podem coexistir com os que você já usa (Snowflake, Dados Externos, Pausado).

---

## 4. Como Atribuir Tarefas

| Pessoa | Tipo de Tarefa |
|--------|---------------|
| **Murilo** | Todas as tarefas operacionais + DataCore + Projetos |
| **Brendon** | Tarefas operacionais delegadas (ingestões, monitoramento) |
| **Olivio** | Apenas tarefas de Banco de Preços e governança (→ apoio ao Flavio) |

---

## 5. Fluxo de Trabalho no Planner

```
Nova demanda chega
       │
       ▼
 ┌─────────────┐
 │  📥 Backlog  │  ← Toda demanda entra aqui
 │  & Triagem   │
 └──────┬──────┘
        │ Classificar + Priorizar
        ▼
 ┌──────────────────────────────────────┐
 │  Mover para o bucket correto:       │
 │  📦 Parceria │ 📊 Coleta │ 🌐 Ext  │
 │  🔍 Consulta │ ☁️ Cloud │ 💻 Proj  │
 └──────┬───────────────────────────────┘
        │ Executar
        ▼
 ┌─────────────┐
 │ ✅ Concluída │  ← Mover ao finalizar
 └─────────────┘
```

---

## 6. Rotina de Gestão do Planner

| Quando | Ação |
|--------|------|
| **Diário (manhã)** | Verificar Backlog, mover tarefas, atualizar checklists |
| **Quarta-feira** | Revisar prazos da semana, priorizar pendências |
| **Sexta-feira** | Mover concluídas para ✅, limpar Backlog, planejar próxima semana |
| **Mensal** | Revisar tarefas recorrentes, atualizar periodicidades, arquivar |

---

## 7. Migração — Passo a Passo

Siga esta sequência para reorganizar o Planner sem perder nada:

### Passo 1: Criar os novos buckets
- Criar: "📦 Dados de Parceria", "🔍 Consultas ao BP", "💻 DataCore & Projetos", "✅ Concluídas"

### Passo 2: Renomear buckets existentes
- "Backlog - Não Iniciadas" → "📥 Backlog & Triagem"
- "Tabelas de Informantes" → "📊 Tabelas de Coleta / Informantes"
- "Recebimento de Dados" → pode ser absorvido por "📦 Dados de Parceria"

### Passo 3: Mover tarefas existentes
- Dados Imobiliários (Divino Imóveis, Moraes) → "📦 Dados de Parceria"
- Wirex Cable, TDM, Saint-Gobain → já estão no bucket correto (agora renomeado)
- Reestruturação Snowflake → permanece em "☁️ Cloud Platform"

### Passo 4: Criar tarefas de monitoramento
- Criar tarefas recorrentes para Neogrid, Pastorinho, Starian
- Criar tarefas para dados externos (CEP, RAIS, CAGED, etc.)

### Passo 5: Configurar rótulos
- Atualizar/criar os rótulos conforme a tabela acima

### Passo 6: Criar tarefa SDIBRE-1149
- Bucket: Cloud Platform
- Prioridade: Alta
- Checklist: ☐ Falar com Victor ☐ Registrar status
