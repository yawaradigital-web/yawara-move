# Yawara Live — infraestrutura v1

## Implementado
- Site demonstrativo hospedado como estático no Render.
- `engine.js`: motor de pontuação independente de TikTok e browser.
- `tests/engine.test.cjs`: testes Node nativos, executar com `node --test tests/engine.test.cjs` dentro de yawara-live.
- `database/schema_v1.sql`: proposta de esquema Postgres com RLS para instalar somente em projeto dedicado Yawara Live.

## Separação de pontuações
- Diretoria: apenas presentes (valor por unidade x quantidade).
- Torcida: curtida e compartilhamento +1; seguir e Heart Me +5 (uma vez); Super Fã +10 (uma vez).
- Score do clube: presentes + torcida. Somente eventos verificados devem entrar em produção.
- Cargos e ordenação são derivados, não privilégios de acesso ao banco.

## Segurança antes de produção
1. Criar projeto Supabase **dedicado** ao Yawara Live; nunca usar o banco Yawara Move.
2. Revisar RLS, privilégios e o modelo de exposição pública antes de aplicar a migração.
3. Construir servidor de ingestão autenticado com chave **secreta apenas no backend**. Nunca aceitar giftPoints/fanPoints enviados pelo navegador como prova de eventos.
4. Validar fonte permitida de eventos da plataforma e tratar replay/idempotência via `source_event_id`.
5. Corrigir verificações cruzadas de partida/clube/participante no backend e definir regras de times/asymmetric battles.
6. Expor placar público por projeção sanitizada, sem identificadores privados.
7. Autorizar apenas criador verificado a iniciar, pausar e finalizar partidas. Adicionar auditoria e limites de taxa.
8. Testar simultaneidade de múltiplos celulares, reconexão, pausas e eventos fora de ordem.
9. Heart Me, Super Fã, curtidas individuais e compartilhamentos individuais não são eventos garantidos: só pontuar automaticamente se a fonte autorizada comprovar.

## Próximo marco
Banco dedicado + ingestão controlada + publicação sanitizada do estado + canal Realtime + login do criador.
O atual site ainda não é multiusuário real: o painel e o Flex compartilham um estado local do navegador.
