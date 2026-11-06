# Yawara Move | Plano de entrega S10 a S17

Status verificado: **sandbox público**, sem transporte ou pagamento real. A marca MOVE e o ícone original são os únicos ativos visuais oficiais. O Design System usa navy profundo, turquesa e branco.

## S10 - Persistência segura
**Preparado, não ativado.** Supabase Yawara Move tem esquema isolado `ym_demo`, tabelas com RLS e acesso de `anon`/`authenticated` negado; fluxo principal validado em PostgreSQL descartável do GitHub Actions. A aplicação Render ainda usa SQLite efêmero. Não ligar `MOVE_STORAGE_BACKEND=postgres` antes de criar credencial restrita, obter endereço exato do Supavisor Session Pooler no Dashboard, inserir segredo diretamente no Render e testar escrita, leitura, reinício e rollback num serviço de staging.

## S11 - Identidade
**Não implementada para clientes reais.** Fluxo fictício tem token temporário e revogação. Próxima arquitetura: Supabase Auth com confirmação de e-mail/telefone, recuperação, MFA para administradores, permissões por função, auditoria de acessos, verificação de documentos com fornecedor habilitado e segregação entre usuários de teste e clientes. Não usar `user_metadata` para autorização; criar e testar policies RLS antes de habilitar usuários reais.

## S12 - Geolocalização, mapas e rotas
**Protótipo de localização opcional e diagrama de pontos.** O MOVE Explore solicita permissão explícita de geolocalização e usa as coordenadas apenas no navegador para identificar o ponto demonstrativo mais próximo. Não transmite a coordenada obtida, nem armazena histórico. O diagrama esquemático não representa ruas, navegação ou percurso real. Para mapa e ETA reais: integrar provedor licenciado/contratado com geocodificação, direções e preços avaliados, consentimento LGPD, políticas de cache e atribuição. Nunca mascarar linha reta como rota de trânsito.

## S13 - Comparador
**Protótipo testável.** Única estimativa disponível: MOVE fictícia; comissão fixa de 10% apenas nas corridas do motorista parceiro. Uber, 99, inDrive, Turbi, BlaBlaCar, Buser, Skyscanner e Lalamove são referências de UX e produto, **não provedores conectados**. Integração futura exige contratos e APIs autorizadas; não fazer scraping, nem exibir ofertas, descontos ou disponibilidade inventados.

## S14 - Motoristas e entregas
**Motorista de teste funcional; entregas conceituais.** Antes de ativar: KYC e documentos, aprovação de veículo, regras e seguros, políticas de cancelamento, segurança, jornada de trabalho, localização em tempo real somente com consentimento e ferramentas antifraude. Carga: descrição, categoria, veículo compatível, múltiplas paradas, cadeia de custódia e prova de entrega, com restrições por região. Não há aceitação de transporte real.

## S15 - Pagamentos
**Emulador fictício funcional.** Asaas Sandbox oficial não configurado. Futuro: credenciais do ambiente oficial de testes guardadas apenas no backend, webhooks assinados e idempotentes, reconciliação, devoluções, impostos, split e antifraude; passar por avaliação jurídica/financeira antes de cobranças reais. Permanecem proibidos `MOVE_PAYMENTS_ENABLED=true` e `MOVE_REAL_DISPATCH=true`.

## S16 - Painel operacional
**Especificado, não ativo.** Backoffice precisa listar corridas por status, controle antifraude, suporte, métricas operacionais, auditoria imutável, governança e exportações autorizadas. Somente funcionários com autenticação forte e papéis auditados. Sem console administrativo público de escrita.

## S17 - Mobile
**Web mobile responsiva com manifesto de demonstração.** MOVE Explore está em `/explore`, acessível via navegador. Não existe APK/IPA nativo pronto nem publicação nas lojas. A PWA não armazena dados sensíveis offline e não registra Service Worker. Futuro: React Native/Expo, permissões mínimas, testes de acessibilidade, compatibilidade, redes lentas, notificações e homologação Play Store/App Store.

## Condições de aceite para piloto real
1. Privacidade e segurança (LGPD, identidade, RLS e proteção contra abuso distribuído).
2. Persistência e backup com restauração comprovada.
3. Geolocalização e ETA reais com provedor contratado e atribuição correta.
4. Integrações de comparação autorizadas, sem preços fictícios.
5. Pagamentos em sandbox oficial com conciliação e ausência de transações reais até autorização.
6. Observabilidade e alertas, testes de carga e validação manual do app mobile.
7. Políticas operacionais, seguros e exigências legais por município/modalidade.

### Equipe virtual de revisão
Os 42 perfis de agentes constituem matriz de especialidades e revisão (produto, branding, UX/UI, front/back, QA, segurança, dados, mapas, operações, financeiro, jurídico e acessibilidade). Não são 42 auditores independentes e não substituem fornecedores licenciados ou homologação humana.
