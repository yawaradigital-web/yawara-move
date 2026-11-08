# TikTok API integration — Yawara Live
Status: prepared receiver; **not a functional TikTok LIVE data feed**.

## Verified official information (2026-11-07)
- Developer webhook documentation lists authorization.removed, video.upload.failed,
  video.publish.completed, portability.download.ready.
- Public documentation reviewed did **not** establish generic LIVE gifts/likes/comments/shares events.
- TikTok developer app access and review required for approved scopes.
- TikTok-Signature is HMAC-SHA256 of `timestamp + "." + raw request body` using client secret.

## Prepared
- Edge Function `tiktok-live-connector` verifies signatures (5-min replay limit) and client key.
- Requires TIKTOK_CLIENT_SECRET and TIKTOK_CLIENT_KEY to be set in Supabase secrets.
- Responds 503 if unconfigured; refuses unsigned/unrecognized traffic.
- **Does not write scores or users**: public LIVE events have not been confirmed.
- GET status reports configured state without exposing keys.

## Steps to enable legitimate LIVE integration
1. Register Yawara Live on https://developers.tiktok.com/ and request relevant approved capabilities.
2. Obtain specific documented access to LIVE interaction events, if offered for the app.
3. Configure TikTok Developer Portal client key/secret as Supabase secrets, never in GitHub.
4. Register the HTTPS callback approved by TikTok, after checking available event types.
5. Implement authorized LIVE adapter with authenticated event IDs, room IDs, stable user IDs and gift combo finalization.
6. Map validated inputs to `yl_events` with idempotency and transactionally applied `yl_participants` points.
7. Keep gift points separate from fan points, and reject unverified individual likes/shares/Heart Me/Super Fã.
8. Test replay, duplicates, invalid signature, reconnection, out-of-order events, time zones and rate limits.

## References
https://developers.tiktok.com/docs/en/webhooks-events
https://developers.tiktok.com/docs/en/webhooks-verification
https://developers.tiktok.com/docs/en/getting-started-faq
