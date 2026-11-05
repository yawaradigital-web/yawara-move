# Yawara Move — Sprint S7: integridade e persistência

## Mudanças entregues

- Índice único parcial para proteger um motorista de aceitar duas viagens simultâneas (SQLite e `ym_demo` no Supabase).
- API responde com HTTP 409 quando a restrição de integridade detecta uma segunda corrida ativa.
- Testes de restrição no banco, consulta de tarifa com comissão demonstrativa fixa de 10% e leitura persistida entre dois processos SQLite.
- Sem alteração de tarifas, UI, autenticação real, motor de despacho real ou pagamentos verdadeiros.

## Validações

- O índice `ym_demo.demo_driver_one_active_idx` foi criado e a definição consultada no projeto Supabase Yawara Move.
- Os testes S6 + S7 passaram localmente no ambiente de desenvolvimento (8 cenários).
- Backend FastAPI compilado e verificado com `compileall`.

## Pendente: troca efetiva para PostgreSQL

O serviço Render usa SQLite em disco temporário. **Não** ativar `MOVE_STORAGE_BACKEND=postgres` até que tudo abaixo esteja validado:

1. Consultar no painel Supabase o endereço **exato** do modo session pooler, não inferir o hostname da região.
2. Estabelecer uma conta PostgreSQL exclusiva, com permissões mínimas restritas ao esquema `ym_demo` e RLS para essa conta. A configuração de criação de role com SQL via conexão disponível foi bloqueada pelas políticas da ferramenta e NÃO foi aplicada.
3. Armazenar credenciais somente no ambiente privado do Render. Nunca registrar senha, URL de conexão ou service-role key no GitHub ou frontend.
4. Testar conexão TLS e inserir/consultar **dados sintéticos**; validar concorrência e sobreviver reinício sem perda.
5. Configurar monitoramento do endpoint `/api/ready` e realizar rollback para SQLite em caso de erro antes de anunciar persistência ativa.

Até a conclusão desses itens, `persistent_storage=false` deverá continuar visível no `/api/health`.

## Limites

Ambiente de demonstração. Nenhum pagamento real, motorista homologado, GPS real ou integração de terceiros. Não contém cadastro seguro para pessoas reais.