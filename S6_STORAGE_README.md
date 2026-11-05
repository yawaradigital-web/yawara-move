# Sprint S6: separacao de dados e backend preparado para PostgreSQL

## Estado verificado
- Supabase existente `Yawara Move` esta ACTIVE_HEALTHY, sem novo servico contratado.
- Schema exclusivo `ym_demo` aplicado, com contas, motoristas, corridas e pagamentos *ficticios*.
- Todas as quatro tabelas possuem RLS habilitado; `anon` e `authenticated` nao recebem acesso ao schema.
- O frontend publico no Render continua com SQLite efemero enquanto credenciais e rede nao forem configuradas.
- API: `GET /api/ready` verifica conexao com o armazenamento; `POST /api/logout` revoga a sessao ficticia.

## Migracao segura para PostgreSQL (AINDA NAO ATIVADA)
- Armazenar uma URI PostgreSQL exclusiva do banco do projeto no segredo de ambiente `DATABASE_URL` no Render; nao inserir em GitHub/HTML/chat.
- Usar conta de banco com privilegios minimos sobre `ym_demo` e acesso TLS protegido; nunca uma chave publica/anon como senha.
- Definir `MOVE_STORAGE_BACKEND=postgres` somente com o segredo presente e apos teste de conectividade e autorizacao do projeto.
- O aplicativo recusa inicializar se o backend PostgreSQL for selecionado sem `DATABASE_URL`; nao ha fallback silencioso.
- Ativar separadamente health check GET `/api/ready`, backup/retencao e limites de acesso.
- Nao migrar tabelas `public.ym_*` nem copiar dados de usuarios para testes.
- Credenciais de banco nao sao geradas nem publicadas por esta entrega.

## Producao bloqueada
`MOVE_REAL_DISPATCH` e `MOVE_PAYMENTS_ENABLED` com valores de ativacao causam falha explicita de inicio.
O calculo de tarifas segue ilustrativo. Sem GPS comercial, Asaas ou viagens reais.

## Limites e proximos gates
- A compatibilidade Postgres foi implementada e validada de forma estatica/mocks, mas NAO passou por teste de integracao com Postgres remoto.
- `ym_demo` teve verificacao de tabelas e RLS via Supabase MCP; `RLS Enabled No Policy` e intencional nesta area isolada.
- Falta conexao de credenciais segura, testes de transacao contra Postgres, persistencia entre deploys, escalabilidade e autenticacao de usuarios reais.