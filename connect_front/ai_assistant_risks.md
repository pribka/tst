# AI Assistant: краткий список рисков и точек для рефакторинга

## Главные риски

1. Front timeout короче backend processing

- фронт ждёт `POST /chat_ai/messages/` только 60 секунд
- backend/LLM может работать намного дольше
- результат: фронт показывает ошибку, хотя бот может позже успешно создать ответ

2. Нет streaming/polling модели

- UI ждёт один длинный HTTP-ответ
- endpoint статуса сообщения есть, но фронт его не использует
- при долгой обработке пользователь видит только общий индикатор

3. Optimistic user-message не reconciled с backend

- сообщение пользователя сразу рисуется локально с временным `uuid`
- серверный id этого сообщения фронт не подменяет
- это усложняет дальнейшую синхронизацию, retry и трекинг статусов

4. Текущий UI живёт только с первым чатом

- backend умеет список чатов
- фронт всегда берёт `results[0]`
- многодиалоговый сценарий фактически не реализован

5. Создание объектов идёт в обход `chat_ai/materialize`

- intents уточняются через `chat_ai`
- но создание сущностей идёт напрямую в бизнесовые endpoint’ы через `metadata.backend_base_url`
- логика завершения intent размазана между `chat_ai` и прикладными модулями

6. Риски по доступам нужно отдельно перепроверить

- `AIChatViewSet` защищён `AIBotEnabled`
- `AIMessageViewSet` и `IntentModelViewSet` выглядят заметно мягче
- стоит отдельно проверить, нельзя ли читать/менять чужие данные по известным id

## Точки для рефакторинга

1. Перевести обработку сообщения на async flow

- быстро возвращать `user_message`
- дальше либо polling по `/messages/<id>/status/`, либо SSE/WebSocket
- bot-message догружать отдельно

2. Синхронизировать timeout-стратегию

- либо увеличить фронтовый timeout
- либо перестать держать длинный синхронный `POST`

3. Ввести нормальный reconciliation сообщений

- временное фронтовое сообщение должно заменяться серверной записью
- это упростит retry, deduplication и аудит

4. Определиться с единой точкой materialization

- либо использовать только `chat_ai/intents/<id>/materialize/`
- либо явно зафиксировать, что `chat_ai` отвечает только за extraction/resolution, а создание всегда делает бизнесовый endpoint

5. Ужесточить и централизовать permission checks

- особенно для messages/intents list/detail/update/delete
- полезно добавить явную фильтрацию queryset по владельцу

6. Разделить transport/UI-state и domain-state

- сейчас в store смешаны:
  - локальные optimistic записи
  - реальные backend messages
  - aiLoading
  - состояние форм intents
- лучше разнести это по более явным слоям

7. Формализовать контракт `intent_type.metadata`

- сейчас frontend сильно завязан на структуру `metadata.fields`, `backend_base_url`, `fixed_values`, `get_parameter`
- стоит описать это как стабильный schema-contract

8. Добавить наблюдаемость pipeline

- полезны trace-id на сообщение
- логирование этапов classify/parse/reply
- отдельные метрики по retry, timeout, failed intents, latency провайдеров
