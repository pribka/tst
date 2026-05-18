# RuleWay Connect Front Decomposition

Источник: локальный документ `RuleWay_ Connect.md` в корне проекта.

Этот пакет декомпозирует регламент RuleWay: Connect на фронтовые тематические блоки. Для каждого блока зафиксированы:
- какие разделы регламента он покрывает;
- какие фронтовые модули уже участвуют;
- чего не хватает по функциональности;
- отдельный файл с заданиями на доработку.

Ограничение этого обследования: только фронт. Бэкенд, интеграции, права и модели данных упоминаются только там, где без них нельзя понять фронтовый разрыв.

## Блоки

1. [Основа системы и объекты управления](./blocks/01-foundation-and-object-model.md)
   Задания: [tasks/01-foundation-and-object-model.md](./tasks/01-foundation-and-object-model.md)
2. [Планирование, задачи и недельный ритм](./blocks/02-planning-tasks-and-weekly-rhythm.md)
   Задания: [tasks/02-planning-tasks-and-weekly-rhythm.md](./tasks/02-planning-tasks-and-weekly-rhythm.md)
3. [Трудозатраты, закрытие недели и отчетность](./blocks/03-time-tracking-and-closing-cycle.md)
   Задания: [tasks/03-time-tracking-and-closing-cycle.md](./tasks/03-time-tracking-and-closing-cycle.md)
4. [Управленческий контур, пульс дня и ИИ-сводки](./blocks/04-manager-control-pulse-and-ai-summaries.md)
   Задания: [tasks/04-manager-control-pulse-and-ai-summaries.md](./tasks/04-manager-control-pulse-and-ai-summaries.md)
5. [Встречи, звонки и внутренние коммуникации](./blocks/05-meetings-calls-and-communications.md)
   Задания: [tasks/05-meetings-calls-and-communications.md](./tasks/05-meetings-calls-and-communications.md)
6. [Клиентские обращения, заявки и согласования](./blocks/06-client-requests-and-request-workflows.md)
   Задания: [tasks/06-client-requests-and-request-workflows.md](./tasks/06-client-requests-and-request-workflows.md)
7. [Паспорта объектов, аналитика и ИИ-оценка](./blocks/07-passports-analytics-and-ai-assessment.md)
   Задания: [tasks/07-passports-analytics-and-ai-assessment.md](./tasks/07-passports-analytics-and-ai-assessment.md)

## Общий вывод

По фронту уже есть хороший фундамент:
- `WorkPlan`, `vue2TaskComponent`, `Calendar`, `HelpDesk`, `Projects`, `Reports`, `Dashboard`, `Notifications`, `AIAssistant`;
- отдельные модули для встреч, чатов, комментариев и файлов;
- справочники и оргструктура в `Directories`, `Groups`, `Profiler`.

Основной разрыв не в отсутствии экранов как таковых, а в отсутствии сквозного пользовательского контура:
- не везде обязательно связываются действия с объектами управления;
- недельный цикл сотрудника и руководителя не собран в единый UX;
- нет выраженного фронтового контура для `висяков`, закрытия недели и управленческих сигналов;
- коммуникации и ИИ уже есть частично, но не собраны в единый процесс;
- цифровые паспорта объектов и ИИ-оценка скорее просматриваются как идея, чем как готовый продуктовый слой.
