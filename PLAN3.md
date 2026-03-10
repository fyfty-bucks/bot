# Phase 3: Telegram Bot

**Status:** NOT STARTED

---

## Scope

Telegram bot: public chat, private features, channel.
Core communication layer for user interaction and future monetization.

## Dependencies

Phase 2 (LLM) — provides response generation

## Spike

- [ ] Bot framework: python-telegram-bot vs aiogram
- [ ] Monetization APIs: Stars, TON, payments
- [ ] Webhook vs polling on RPi constraints

## Deliverables

- [ ] Public chat: request — tools + LLM — response
- [ ] Private chat: premium features (subscription model)
- [ ] Channel: scheduled posts, reports, metrics
- [ ] User interaction tracking (likes, messages, payments)
- [ ] Error routing: user-facing / owner-only / self-fixable
- [ ] Bot legend: character, backstory, voice

## Risks

- Telegram API rate limits
- Bot blocking/restrictions
- User retention without clear value proposition

## Gate

Bot operational in public chat. Channel posts automated. User tracking active.
