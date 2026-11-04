# Yawara MOVE — demonstração gratuita na nuvem (S2)

Este pacote adapta o MVP FastAPI S1 para **Render Free**, sem alterar o código de produção inexistente.

## Publicação pelo GitHub + Render
1. Crie um repositório **privado** no GitHub, por exemplo `yawara-move-demo`.
2. Envie o **conteúdo desta pasta** à raiz do repositório (não envie bancos, `.env` ou credenciais).
3. No Render, conecte o GitHub e selecione **New > Blueprint**; aponte para o repositório contendo `render.yaml`.
4. Revise **plan: free** e confirme que pagamentos e mapas externos permanecem desativados.
5. Quando terminar o deploy, abra a URL indicada pelo Render e acesse `/api/health`: deve retornar `payments_enabled:false`, `external_maps_enabled:false` e `real_dispatch_enabled:false`.
6. Cadastre somente perfis **fictícios** e execute uma viagem de demonstração. Não informe nome real, CPF, telefone, cartão ou localização pessoal.

## Limitações importantes
- Render Free pode hibernar após 15 minutos sem tráfego.
- O SQLite em `/tmp` é **efêmero**. Dados se perdem em reinícios, hibernação ou redeploy. Isso é proposital para um laboratório; **não use para dados reais**.
- Aplicação demo não possui autenticação robusta para usuários reais, antifraude, verificação de motoristas, mapas reais, GPS ao vivo, gateway oficial nem autorização operacional.
- URL pública pode receber tráfego e abuso. Não divulgue até implementar controles adicionais.
- A camada gratuita possui limites de horas, banda e recursos; confirme as condições antes de ativar qualquer cobrança.
- Nenhuma ferramenta pode vincular sozinha suas contas Render/GitHub sem a autorização dessas plataformas.

## Verificação local independente
`pip install -r requirements.txt pytest httpx` e `python -m pytest -q tests/test_mvp.py`.

## Evolução para piloto real
Migrar para PostgreSQL gerenciado persistente, autenticação forte, observabilidade, rate limiting, validação de motoristas, política de privacidade e integração oficial de mapas e pagamentos.