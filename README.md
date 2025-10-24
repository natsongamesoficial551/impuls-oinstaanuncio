# 📋 Configuração do Supabase para o Bot

## 🎯 PASSO 1: Criar as Tabelas no Banco de Dados

Você já está na dashboard do Supabase. Agora vamos criar as tabelas:

### 1.1 - Abrir o Editor SQL

1. No menu lateral **ESQUERDO**, procure o ícone que parece **</>** (SQL)
2. Clique em **"SQL Editor"** ou **"Editor SQL"**
3. Você verá uma tela para escrever código SQL

### 1.2 - Criar Nova Query

1. Clique no botão **"+ New query"** ou **"+ Nova consulta"** (canto superior)
2. Uma tela em branco vai abrir para você colar o código

### 1.3 - Colar o Código SQL

Copie **TODO** o código abaixo e cole na tela do SQL Editor:

```sql
-- Tabela de pedidos (armazena todos os comprovantes enviados)
CREATE TABLE pedidos (
    id BIGSERIAL PRIMARY KEY,
    pedido_id TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    pedido_number INTEGER,
    plano TEXT NOT NULL,
    status TEXT NOT NULL,
    moderador_id BIGINT,
    moderador_nome TEXT,
    canal_id BIGINT,
    comprovante_path TEXT,
    motivo_reprovacao TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    fechado_em TIMESTAMPTZ,
    fechado_por BIGINT
);

-- Tabela de contador sequencial (para numeração dos pedidos)
CREATE TABLE contador (
    id INTEGER PRIMARY KEY DEFAULT 1,
    ultimo_numero INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT single_row CHECK (id = 1)
);

-- Inserir contador inicial
INSERT INTO contador (id, ultimo_numero) VALUES (1, 0);

-- Índices para melhor performance
CREATE INDEX idx_pedidos_pedido_id ON pedidos(pedido_id);
CREATE INDEX idx_pedidos_user_id ON pedidos(user_id);
CREATE INDEX idx_pedidos_status ON pedidos(status);
```

### 1.4 - Executar o Código

1. Após colar o código, clique no botão **"Run"** ou **"Executar"** (geralmente no canto superior direito)
2. Você verá uma mensagem: **"Success. No rows returned"** ✅
3. Isso significa que as tabelas foram criadas com sucesso!

---

## 🔑 PASSO 2: Pegar as Credenciais do Supabase

Agora você precisa pegar 2 informações importantes: **URL** e **KEY**

### 2.1 - Abrir Configurações

1. No menu lateral **ESQUERDO**, clique no ícone de **engrenagem** ⚙️ (Settings/Configurações)
2. Clique em **"API"**

### 2.2 - Copiar a URL do Projeto

1. Procure a seção **"Project URL"** ou **"URL do projeto"**
2. Você verá algo como:
   ```
   https://vmsmcsujbbkglzccsqic.supabase.co
   ```
3. **COPIE** essa URL completa (clique no ícone de copiar ao lado)
4. **GUARDE** em algum lugar seguro (bloco de notas)

### 2.3 - Copiar a Chave Anon/Public

1. Na mesma página, procure **"Project API keys"** ou **"Chaves de API do projeto"**
2. Você verá duas chaves:
   - `service_role` (secreta) ❌ **NÃO USE ESSA**
   - `anon` `public` ✅ **USE ESSA**
3. Copie a chave **"anon"** ou **"public"** (é uma chave longa que começa com `eyJ...`)
4. **GUARDE** junto com a URL

Exemplo da chave:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtc21jc3VqYmJrZ2x6Y2NzcWljIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTg3NjU0MzIsImV4cCI6MjAxNDM0MTQzMn0.abc123def456...
```

---

## ✅ PASSO 3: Verificar se Funcionou

### 3.1 - Verificar Tabelas Criadas

1. No menu lateral esquerdo, clique em **"Table Editor"** ou **"Editor de tabela"**
2. Você deve ver **2 tabelas**:
   - ✅ `pedidos`
   - ✅ `contador`
3. Clique em cada uma para ver as colunas criadas

### 3.2 - Verificar Contador Inicial

1. Clique na tabela **`contador`**
2. Você deve ver **1 linha** com:
   - `id`: 1
   - `ultimo_numero`: 0

---

## 🎉 Pronto! Supabase Configurado

Agora você tem:
- ✅ 2 tabelas criadas no banco de dados
- ✅ URL do projeto: `https://vmsmcsujbbkglzccsqic.supabase.co`
- ✅ Chave Anon/Public: `eyJ...`

---

## 📝 Próximos Passos

Você vai precisar dessas informações para configurar o bot:

### No arquivo `.env` (localmente):
```env
SUPABASE_URL=https://vmsmcsujbbkglzccsqic.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### No Render (variáveis de ambiente):
- Adicione `SUPABASE_URL` = sua URL
- Adicione `SUPABASE_KEY` = sua chave anon

---

## ⚠️ IMPORTANTE

- **NUNCA** compartilhe sua chave `service_role` (a outra chave)
- Use **APENAS** a chave `anon` ou `public`
- Não commite o arquivo `.env` no GitHub (já está no `.gitignore`)

---

## 🆘 Deu Erro?

### Erro: "relation already exists"
- Significa que a tabela já foi criada antes
- Solução: Ignore o erro, as tabelas já existem

### Erro: "permission denied"
- Verifique se está logado no Supabase
- Tente fazer logout e login novamente

### Tabelas não aparecem
- Clique em **"Refresh"** ou **"Atualizar"** no Table Editor
- Aguarde 10-20 segundos e recarregue a página