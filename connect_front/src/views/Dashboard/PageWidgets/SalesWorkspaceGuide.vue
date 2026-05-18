<template>
    <div
        class="sales_guide"
        :class="{ 'sales_guide--floating': floating }">
        <button
            ref="entry"
            type="button"
            class="sales_guide__entry"
            data-guide-id="sales-guide-entry"
            :style="entryStyle"
            @mousedown="startEntryDrag"
            @touchstart="startEntryDrag"
            @click="handleEntryClick">
            <span>
                <b>CRM-процесс</b>
                <em>Лид → интерес → заказ</em>
            </span>
            <i class="fi fi-rr-route" />
        </button>

        <div
            v-if="active"
            class="sales_guide__mask"
            @click="next" />
        <div
            v-if="active && targetRect"
            class="sales_guide__spot"
            :style="spotStyle" />
        <section
            v-if="active"
            ref="panel"
            class="sales_guide__panel"
            :style="panelStyle">
            <div
                class="sales_guide__progress"
                @mousedown.stop="startPanelDrag"
                @touchstart.stop="startPanelDrag">
                <span>{{ currentIndex + 1 }} / {{ visibleSteps.length }}</span>
                <button type="button" @click="finish">Закрыть</button>
            </div>
            <h2>{{ currentStep.title }}</h2>
            <p>{{ currentStep.text }}</p>
            <ul
                v-if="currentStep.points && currentStep.points.length"
                class="sales_guide__points">
                <li
                    v-for="point in currentStep.points"
                    :key="point">
                    {{ point }}
                </li>
            </ul>
            <div class="sales_guide__hint">
                {{ currentStep.hint }}
            </div>
            <div class="sales_guide__dots">
                <span
                    v-for="(step, index) in visibleSteps"
                    :key="step.key"
                    :class="{ active: index === currentIndex }" />
            </div>
            <div class="sales_guide__actions">
                <button
                    type="button"
                    :disabled="currentIndex === 0"
                    @click="prev">
                    Назад
                </button>
                <button
                    type="button"
                    class="sales_guide__primary"
                    @click="next">
                    {{ currentIndex === visibleSteps.length - 1 ? 'Готово' : 'Дальше' }}
                </button>
            </div>
        </section>
    </div>
</template>

<script>
export default {
    name: 'SalesWorkspaceGuide',
    props: {
        floating: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            active: false,
            currentIndex: 0,
            targetRect: null,
            domTick: 0,
            panelPosition: null,
            entryPosition: null,
            dragState: null,
            suppressEntryClick: false,
            steps: [
                {
                    key: 'entry',
                    selector: '[data-guide-id="sales-guide-entry"]',
                    title: 'CRM-процесс',
                    text: 'Основная цепочка продаж: лид → интерес → клиент → потребности → заказ.',
                    points: [
                        'Лид фиксирует входящий запрос до квалификации.',
                        'Интерес хранит предмет сделки, клиента и потребности.',
                        'Заказ оформляется по проверенным потребностям клиента.'
                    ],
                    hint: 'Стадия сделки должна подтверждаться данными: клиентом, потребностями, контрактом или заказом.'
                },
                {
                    key: 'nav',
                    selector: '[data-guide-id="sales-main-nav"]',
                    title: 'Разделы продаж',
                    text: 'Разделы разделены по типам работы в CRM.',
                    points: [
                        'Рабочий стол: текущие объекты, которым нужен следующий шаг.',
                        'Лиды: входящие обращения до создания интереса.',
                        'Интересы: сделки до заказа.',
                        'Воронка: распределение лидов и интересов по недостающим фактам.'
                    ],
                    hint: 'Клиенты, заказы и отчеты используются после квалификации интереса.'
                },
                {
                    key: 'quickCreate',
                    selector: '[data-guide-id="sales-quick-create"]',
                    title: 'Ручное создание',
                    text: 'Кнопки используются, когда объект появился вне автоматического потока.',
                    points: [
                        'Лид: есть обращение, но еще нет подтвержденного предмета сделки.',
                        'Интерес: предмет сделки уже понятен.',
                        'Заказ: клиент и потребности готовы к оформлению.'
                    ],
                    hint: 'Если продажа пришла через обращение, лучше начинать с лида: система сохранит исходный контекст.'
                },
                {
                    key: 'leftFilters',
                    selector: '[data-guide-id="sales-left-filters"]',
                    title: 'Фильтры действий',
                    text: 'Фильтры показывают, какого факта не хватает объектам.',
                    points: [
                        'Новые лиды: нужно создать или открыть интерес.',
                        'Нет клиента: нужна карточка клиента.',
                        'Нет потребностей: нужна таблица потребностей.',
                        'К заказу: потребности есть, заказа еще нет.'
                    ],
                    hint: 'Фильтр не меняет данные, а ограничивает рабочую очередь.'
                },
                {
                    key: 'kpi',
                    selector: '[data-guide-id="sales-kpi"]',
                    title: 'Рабочие счетчики',
                    text: 'Счетчики показывают объекты, по которым есть незакрытый следующий шаг.',
                    points: [
                        'Разобрать лиды: входящие обращения без завершенной квалификации.',
                        'Интересы в работе: активные сделки.',
                        'Уточнить клиента: интересы без карточки клиента.',
                        'Выявить потребности: интересы без строк потребностей.',
                        'Оформить заказ: интересы с потребностями без заказа.'
                    ],
                    hint: 'Рост счетчика означает накопление незавершенной работы на конкретном этапе.'
                },
                {
                    key: 'sevenChains',
                    selector: '[data-guide-id="sales-seven-chains"]',
                    title: '7 рабочих цепочек',
                    text: 'Блок показывает семь ближайших CRM-цепочек и состояние каждого этапа.',
                    points: [
                        'Карточка начинается с текущего объекта: лида, интереса или заказа.',
                        'Зеленые этапы уже подтверждены данными.',
                        'Синий этап показывает, где цепочка сейчас остановилась.',
                        'Кнопка справа выполняет следующий допустимый шаг.',
                        'Авторазбор обрабатывает видимые лиды и интересы, где не нужен ручной выбор клиента.'
                    ],
                    hint: 'Цель блока — убрать лишние переходы: менеджер идет по цепочке одной кнопкой.'
                },
                {
                    key: 'sevenChainCard',
                    selector: '[data-guide-id="sales-seven-chain-card"]',
                    title: 'Карточка цепочки',
                    text: 'Карточка связывает лид, интерес, клиента, потребности, контракт и заказ.',
                    points: [
                        'Название открывает текущий объект.',
                        'Причина объясняет, чего не хватает для движения дальше.',
                        'Создать интерес, LLM-потребности и оформить заказ запускаются отсюда.',
                        'Если заказ уже создан, действие открывает заказ.'
                    ],
                    hint: 'По этой карточке видно не только “что нажать”, но и какой факт CRM должен появиться.'
                },
                {
                    key: 'attention',
                    selector: '[data-guide-id="sales-attention"]',
                    title: 'Очередь решений',
                    text: 'Таблица объединяет лиды и интересы, где требуется действие менеджера.',
                    points: [
                        'Тип показывает сущность: лид, интерес или заказ.',
                        'Клиент показывает привязку к карточке CRM.',
                        'Причина объясняет, какого факта не хватает.',
                        'Ответственный показывает, кто должен закрыть следующий шаг.'
                    ],
                    hint: 'Строка остается в очереди, пока не появится недостающий факт.'
                },
                {
                    key: 'action',
                    selector: '[data-guide-id="sales-next-action"]',
                    title: 'Действие строки',
                    text: 'Кнопка выполняет следующий допустимый шаг для текущего состояния.',
                    points: [
                        'LLM-анализ лида создает интерес и переносит контекст обращения.',
                        'LLM-потребности заполняют таблицу потребностей интереса.',
                        'Оформить заказ используется после заполнения потребностей.',
                        'Открыть интерес ведет к уже созданной сделке.'
                    ],
                    hint: 'Повторное создание интереса по тому же лиду не должно плодить дубликаты.'
                },
                {
                    key: 'newLeads',
                    selector: '[data-guide-id="sales-new-leads"]',
                    title: 'Новые лиды',
                    text: 'Лид — входящее обращение, которое еще не стало полноценной сделкой.',
                    points: [
                        'Источник: HelpDesk-обращение с типом lead.',
                        'Контекст: описание, клиент, контактное лицо и сообщения.',
                        'Результат анализа: интерес и список потребностей.',
                        'Связь сохраняется через исходный лид.'
                    ],
                    hint: 'Лид без коммерческого смысла не должен уходить дальше по CRM-цепочке.'
                },
                {
                    key: 'interests',
                    selector: '[data-guide-id="sales-active-interests"]',
                    title: 'Активные интересы',
                    text: 'Интерес — рабочая сущность сделки до оформления заказа.',
                    points: [
                        'Клиент нужен для договора и заказа.',
                        'Потребности нужны для состава будущего заказа.',
                        'Стадия зависит от заполненных данных.',
                        'Следующий шаг показывает ближайший недостающий факт.'
                    ],
                    hint: 'Интерес без клиента или потребностей нельзя считать готовым к оформлению.'
                },
                {
                    key: 'readyOrders',
                    selector: '[data-guide-id="sales-ready-orders"]',
                    title: 'Ожидают оформления',
                    text: 'Сюда попадают интересы, у которых уже есть проверенные потребности.',
                    points: [
                        'Потребности переносятся в заказ как состав работ, услуг или товаров.',
                        'Клиент должен быть определен до оформления.',
                        'Заказ фиксирует операционную часть сделки.'
                    ],
                    hint: 'Если заказ уже создан, интерес больше не должен висеть как требующий оформления.'
                },
                {
                    key: 'ordersFlow',
                    selector: '[data-guide-id="sales-orders-flow"]',
                    title: 'Цепочка заказа',
                    text: 'Раздел заказов показывает переход от подготовленного интереса к оформлению.',
                    points: [
                        'Интерес дает клиента и потребности.',
                        'Заказ фиксирует позиции, оплату, доставку и договор.',
                        'После оформления контролируются оплата, доставка и отгрузка.'
                    ],
                    hint: 'Заказ создается не вместо интереса, а на основании уже выявленных потребностей клиента.'
                },
                {
                    key: 'ordersSummary',
                    selector: '[data-guide-id="sales-orders-summary"]',
                    title: 'Состояние заказов',
                    text: 'Счетчики помогают понять, какие заказы требуют внимания после оформления.',
                    points: [
                        'Всего в работе: активные продажи, которые еще не закрыты.',
                        'Ждут оплаты: заказ оформлен, но деньги не зафиксированы.',
                        'Не доставлены: товар или услуга еще не переданы клиенту.'
                    ],
                    hint: 'Эти показатели относятся уже к заказам, а не к лидам или интересам.'
                },
                {
                    key: 'ordersRules',
                    selector: '[data-guide-id="sales-orders-rules"]',
                    title: 'Контроль перед оформлением',
                    text: 'Перед заказом должны быть понятны клиент, позиции и условия исполнения.',
                    points: [
                        'Клиент: CRM-карточка и внешний клиент для договора/учета.',
                        'Позиции: товары или услуги, количество, цена и склад.',
                        'Исполнение: оплата, доставка и отгрузка.'
                    ],
                    hint: 'Если одного из этих фактов нет, заказ лучше не оформлять как полноценный.'
                },
                {
                    key: 'ordersList',
                    selector: '[data-guide-id="sales-orders-list"]',
                    title: 'Список заказов',
                    text: 'Таблица показывает уже оформленные заказы продаж.',
                    points: [
                        'Строка заказа хранит клиента, договор, сумму и состав.',
                        'Заказ может быть открыт для проверки оплаты, доставки и документов.',
                        'По заказу дальше отслеживается отгрузка.'
                    ],
                    hint: 'После создания из интереса заказ должен быть виден здесь и связан с исходной сделкой.'
                },
                {
                    key: 'rightSummary',
                    selector: '[data-guide-id="sales-right-summary"]',
                    title: 'Активность сегодня',
                    text: 'Блок показывает текущую нагрузку по объектам, требующим действий.',
                    points: [
                        'Внимание: все строки в рабочей очереди.',
                        'Новые лиды: необработанный входящий поток.',
                        'Без шага: интересы без ближайшего действия.',
                        'К заказу: интересы, готовые к оформлению.'
                    ],
                    hint: 'Эти числа должны быстро уменьшаться после обработки очереди.'
                },
                {
                    key: 'rightPipeline',
                    selector: '[data-guide-id="sales-right-pipeline"]',
                    title: 'Мини-воронка',
                    text: 'Сводка показывает распределение активных интересов по статусам.',
                    points: [
                        'Количество показывает нагрузку в каждой стадии.',
                        'Сумма в работе считается по активным интересам.',
                        'Большое скопление в стадии означает блокировку процесса.'
                    ],
                    hint: 'Для причины блокировки открывайте полную воронку или деталку интереса.'
                },
                {
                    key: 'shortcuts',
                    selector: '[data-guide-id="sales-shortcuts"]',
                    title: 'Быстрые переходы',
                    text: 'Переходы ведут в разделы для предметной работы.',
                    points: [
                        'Воронка: разбор стадии сделки.',
                        'Обработать лиды: входящие обращения.',
                        'Клиенты: карточки клиентов CRM.'
                    ],
                    hint: 'Переход не меняет объект, а открывает профильный раздел.'
                },
                {
                    key: 'chain',
                    selector: '[data-guide-id="sales-left-chain"]',
                    title: 'Цепочка CRM',
                    text: 'Цепочка показывает основные сущности CRM в порядке обработки.',
                    points: [
                        'Лид может породить интерес.',
                        'Интерес выявляет клиента и потребности.',
                        'Контракт относится к клиенту.',
                        'Заказ создается по потребностям клиента.'
                    ],
                    hint: 'ContractorModel не должен использоваться как CRM-контрагент в этой цепочке.'
                },
                {
                    key: 'funnelBoard',
                    selector: '[data-guide-id="sales-funnel-board"]',
                    title: 'Воронка по фактам',
                    text: 'Колонка воронки определяется недостающим фактом.',
                    points: [
                        'Получение: лиды без созданного интереса.',
                        'Клиент: интересы без карточки клиента.',
                        'Потребности: интересы без строк потребностей.',
                        'Заказ: интересы с потребностями без заказа.'
                    ],
                    hint: 'Ручная смена статуса не заменяет клиента, потребности, договор или заказ.'
                },
                {
                    key: 'funnelCreateInterest',
                    selector: '[data-guide-id="sales-funnel-create-interest"]',
                    title: 'Лид в интерес',
                    text: 'Создание интереса запускает квалификацию лида.',
                    points: [
                        'Берется описание обращения, клиент, контакт и сообщения.',
                        'LLM выделяет предмет интереса.',
                        'Потребности сопоставляются с каталогом.',
                        'Интерес получает ссылку на исходный лид.'
                    ],
                    hint: 'Ручной запуск использует тот же обработчик, что и автоматическая очередь.'
                },
                {
                    key: 'funnelRail',
                    selector: '[data-guide-id="sales-funnel-card-rail"]',
                    title: 'Факты сделки',
                    text: 'Индикаторы на карточке показывают, какие части цепочки уже заполнены.',
                    points: [
                        'Источник: лид или ручное создание.',
                        'Клиент: привязанная карточка CRM.',
                        'Потребности: строки товаров или услуг.',
                        'Контракт и заказ: последующие этапы.'
                    ],
                    hint: 'Активный индикатор соответствует текущему месту объекта в воронке.'
                },
                {
                    key: 'detailTitle',
                    selector: '[data-guide-id="interest-detail-title"]',
                    title: 'Карточка интереса',
                    text: 'Карточка содержит конкретную сделку до этапа заказа.',
                    points: [
                        'Название отражает предмет запроса.',
                        'Описание хранит исходный контекст.',
                        'Клиент связывает интерес с CRM-карточкой.',
                        'Связанный лид остается источником происхождения.'
                    ],
                    hint: 'Если предмет сделки непонятен, нужно уточнить описание до оформления заказа.'
                },
                {
                    key: 'detailStatus',
                    selector: '[data-guide-id="interest-status-flow"]',
                    title: 'Статус интереса',
                    text: 'Статус отражает рабочую фазу обработки интереса.',
                    points: [
                        'Получение интереса: первичный разбор.',
                        'Переговоры: уточнение клиента и потребностей.',
                        'В работе: подготовка оформления.',
                        'Завершено успешно или неуспешно: итог обработки.'
                    ],
                    hint: 'Статус не подменяет факты CRM: клиента, потребности, договор и заказ.'
                },
                {
                    key: 'detailTabs',
                    selector: '[data-guide-id="interest-detail-tabs"]',
                    title: 'Вкладки интереса',
                    text: 'Вкладки разделяют данные интереса по назначению.',
                    points: [
                        'Задача: описание, комментарии, общий контекст.',
                        'Трудозатраты: фактическая работа по интересу.',
                        'Файлы: материалы и вложения.',
                        'Потребности: товары и услуги, которые нужны клиенту.'
                    ],
                    hint: 'Для перехода к заказу важнее всего вкладка “Потребности”.'
                },
                {
                    key: 'interestDescription',
                    selector: '[data-guide-id="interest-description"]',
                    title: 'Контекст интереса',
                    text: 'Описание должно фиксировать, зачем клиент обратился.',
                    points: [
                        'Источник: текст лида или ручное описание менеджера.',
                        'Используется при LLM-анализе потребностей.',
                        'Должно содержать предмет запроса, ограничения и важные детали.'
                    ],
                    hint: 'Плохое описание дает плохие потребности, даже если каталог заполнен.'
                },
                {
                    key: 'needsLlm',
                    selector: '[data-guide-id="interest-needs-llm"]',
                    title: 'LLM-анализ потребностей',
                    text: 'Анализ заполняет потребности по контексту интереса.',
                    points: [
                        'На вход идут описание интереса, клиент и каталог товаров/услуг.',
                        'LLM выделяет потребности клиента.',
                        'Система пытается сопоставить потребность с номенклатурой.',
                        'Заполненные потребности не затираются обычным повторным запуском.'
                    ],
                    hint: 'Если товар не найден, потребность остается без позиции каталога, но с комментарием.'
                },
                {
                    key: 'needsTable',
                    selector: '[data-guide-id="interest-needs-table"]',
                    title: 'Таблица потребностей',
                    text: 'Таблица хранит состав того, что нужно клиенту.',
                    points: [
                        'Потребность: формулировка запроса клиента.',
                        'Товар или услуга: связь с каталогом.',
                        'Количество и цена: расчет будущего заказа.',
                        'Комментарий: исходная человеческая формулировка интереса.'
                    ],
                    hint: 'Заказ должен формироваться из проверенных строк этой таблицы.'
                },
                {
                    key: 'orderProcess',
                    selector: '[data-guide-id="crm-order-process"]',
                    title: 'Оформление заказа',
                    text: 'Шаги сверху показывают, какие факты уже есть для оформления.',
                    points: [
                        'Контрагент и интерес подтверждают источник заказа.',
                        'Товары показывают, что потребности перенесены в состав.',
                        'Доставка и оплата заполняются до финального оформления.'
                    ],
                    hint: 'Если шаг не заполнен, заказ остается черновиком и его нужно дособрать.'
                },
                {
                    key: 'orderSource',
                    selector: '[data-guide-id="crm-order-source"]',
                    title: 'Источник заказа',
                    text: 'Блок фиксирует, откуда пришел заказ в CRM-цепочке.',
                    points: [
                        'Интерес остается исходной сделкой и хранит потребности.',
                        'CRM-договор связывает заказ с клиентом.',
                        'После оформления сумма заказанного обновляет прогресс договора.'
                    ],
                    hint: 'Источник нужен, чтобы потом видеть путь от лида и интереса до заказа.'
                },
                {
                    key: 'orderCustomer',
                    selector: '[data-guide-id="crm-order-customer"]',
                    title: 'Клиент и договор',
                    text: 'Здесь выбирается клиентская основа заказа.',
                    points: [
                        'Клиент приходит из CRM-карточки интереса.',
                        'Договор определяет внешний учетный контур и доступные условия.',
                        'Если договора нет, заказ нельзя считать полностью готовым к исполнению.'
                    ],
                    hint: 'Контракт заключается с клиентом, а не с интересом.'
                },
                {
                    key: 'orderCart',
                    selector: '[data-guide-id="crm-order-cart"]',
                    title: 'Состав заказа',
                    text: 'Позиции заказа должны соответствовать согласованным потребностям.',
                    points: [
                        'Товар или услуга берется из каталога.',
                        'Количество и цена могут отличаться от первоначальной потребности после согласования.',
                        'Склад нужен для дальнейшей отгрузки.'
                    ],
                    hint: 'Заказ может включать не все потребности, если часть не согласована с клиентом.'
                },
                {
                    key: 'orderDelivery',
                    selector: '[data-guide-id="crm-order-delivery"]',
                    title: 'Доставка',
                    text: 'Доставка описывает, как заказ будет передан клиенту.',
                    points: [
                        'Доставка требует адрес и условия передачи.',
                        'Самовывоз оставляет заказ без адреса доставки.',
                        'Склад отгрузки берется из позиций заказа.'
                    ],
                    hint: 'Эти данные нужны для передачи заказа клиенту после оформления.'
                },
                {
                    key: 'orderPayment',
                    selector: '[data-guide-id="crm-order-payment"]',
                    title: 'Оплата и комментарий',
                    text: 'Оплата фиксирует финансовые ожидания по заказу.',
                    points: [
                        'К оплате заполняется после расчета.',
                        'Плановая дата оплаты помогает контролировать задолженность.',
                        'Комментарий сохраняет условия, которые важны для исполнения.'
                    ],
                    hint: 'После расчета заказ можно оформить, если обязательные данные заполнены.'
                },
                {
                    key: 'orderSummary',
                    selector: '[data-guide-id="crm-order-summary"]',
                    title: 'Итог заказа',
                    text: 'Правая панель показывает расчет и готовность к оформлению.',
                    points: [
                        'Рассчитать цены проверяет состав, скидки, НДС и суммы.',
                        'После успешного расчета кнопка оформления становится доступной.',
                        'Лимиты и остатки договора показываются здесь же, если backend их вернул.'
                    ],
                    hint: 'Без расчета заказ не должен уходить в финальное оформление.'
                },
                {
                    key: 'orderSubmit',
                    selector: '[data-guide-id="crm-order-submit"]',
                    title: 'Оформить заказ',
                    text: 'Финальное действие создает заказ продаж по текущему составу.',
                    points: [
                        'Заказ получает связь с интересом и CRM-договором.',
                        'Позиции фиксируются как предмет заказа.',
                        'После создания заказ появляется в списке продаж для контроля оплаты и отгрузки.'
                    ],
                    hint: 'Перед нажатием проверьте клиента, договор, позиции, оплату и доставку.'
                },
                {
                    key: 'orderAfterSubmit',
                    selector: '[data-guide-id="crm-order-after-submit"]',
                    title: 'После оформления',
                    text: 'После создания заказ переходит в операционный контур.',
                    points: [
                        'Заказ виден в списке продаж.',
                        'По нему можно контролировать оплату и отгрузку.'
                    ],
                    hint: 'Интерес после оформления не должен оставаться в очереди “к заказу”.'
                }
            ]
        }
    },
    computed: {
        visibleSteps() {
            this.domTick
            return this.steps.filter(step => this.getTarget(step.selector))
        },
        currentStep() {
            return this.visibleSteps[this.currentIndex] || this.steps[0]
        },
        spotStyle() {
            const rect = this.targetRect
            if (!rect) return {}
            return {
                top: `${rect.top - 7}px`,
                left: `${rect.left - 7}px`,
                width: `${rect.width + 14}px`,
                height: `${rect.height + 14}px`
            }
        },
        entryStyle() {
            if (!this.entryPosition) return {}
            return {
                top: `${this.entryPosition.top}px`,
                left: `${this.entryPosition.left}px`,
                right: 'auto',
                bottom: 'auto'
            }
        },
        panelStyle() {
            const panelWidth = Math.min(430, window.innerWidth - 24)
            if (this.panelPosition) {
                return {
                    top: `${this.panelPosition.top}px`,
                    left: `${this.panelPosition.left}px`,
                    width: `${panelWidth}px`
                }
            }
            const rect = this.targetRect
            if (!rect) {
                return {
                    top: '18px',
                    left: `${Math.max(12, window.innerWidth - panelWidth - 18)}px`,
                    width: `${panelWidth}px`
                }
            }
            const preferRight = rect.left + rect.width + panelWidth + 24 < window.innerWidth
            const preferBelow = rect.bottom + 300 < window.innerHeight
            const top = preferBelow
                ? rect.bottom + 14
                : Math.max(12, Math.min(rect.top, window.innerHeight - 340))
            const left = preferRight
                ? rect.left + rect.width + 14
                : Math.max(12, Math.min(rect.left, window.innerWidth - panelWidth - 12))
            return {
                top: `${top}px`,
                left: `${left}px`,
                width: `${panelWidth}px`
            }
        }
    },
    mounted() {
        window.addEventListener('resize', this.handleResize)
        window.addEventListener('scroll', this.updatePosition, true)
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize)
        window.removeEventListener('scroll', this.updatePosition, true)
        this.removeDragListeners()
    },
    methods: {
        handleEntryClick(event) {
            if (this.suppressEntryClick) {
                this.suppressEntryClick = false
                event.preventDefault()
                event.stopPropagation()
                return
            }
            this.start()
        },
        start() {
            this.currentIndex = 0
            this.active = true
            this.$nextTick(() => {
                this.clampFloatingPositions()
                this.refreshVisibleSteps()
                this.updatePosition()
                window.setTimeout(() => {
                    this.refreshVisibleSteps()
                    this.updatePosition()
                }, 900)
                window.setTimeout(() => {
                    this.refreshVisibleSteps()
                    this.updatePosition()
                }, 2200)
            })
            localStorage.setItem('sales_workspace_guide_seen', '1')
        },
        finish() {
            this.active = false
            this.targetRect = null
        },
        next() {
            if (this.currentIndex >= this.visibleSteps.length - 1) {
                this.finish()
                return
            }
            this.currentIndex += 1
            this.$nextTick(() => this.updatePosition())
        },
        prev() {
            if (this.currentIndex === 0) return
            this.currentIndex -= 1
            this.$nextTick(() => this.updatePosition())
        },
        startEntryDrag(event) {
            if (!this.floating) return
            this.beginDrag(event, 'entry')
        },
        startPanelDrag(event) {
            if (event.target && event.target.closest && event.target.closest('button')) return
            this.beginDrag(event, 'panel')
        },
        beginDrag(event, type) {
            if (event.button !== undefined && event.button !== 0) return
            const point = this.getDragPoint(event)
            const element = type === 'panel' ? this.$refs.panel : this.$refs.entry
            if (!point || !element) return

            const rect = element.getBoundingClientRect()
            this.removeDragListeners()
            this.dragState = {
                type,
                startX: point.x,
                startY: point.y,
                startLeft: rect.left,
                startTop: rect.top,
                width: rect.width,
                height: rect.height,
                moved: false
            }

            if (type === 'panel') {
                this.panelPosition = { left: rect.left, top: rect.top }
            } else {
                this.entryPosition = { left: rect.left, top: rect.top }
            }

            document.addEventListener('mousemove', this.moveDrag)
            document.addEventListener('mouseup', this.finishDrag)
            document.addEventListener('touchmove', this.moveDrag, { passive: false })
            document.addEventListener('touchend', this.finishDrag)
            document.addEventListener('touchcancel', this.finishDrag)
        },
        moveDrag(event) {
            if (!this.dragState) return
            const point = this.getDragPoint(event)
            if (!point) return

            const deltaX = point.x - this.dragState.startX
            const deltaY = point.y - this.dragState.startY
            if (Math.abs(deltaX) > 2 || Math.abs(deltaY) > 2) {
                this.dragState.moved = true
            }

            if (event.cancelable) {
                event.preventDefault()
            }

            const position = this.clampFloatingPosition(
                this.dragState.startLeft + deltaX,
                this.dragState.startTop + deltaY,
                this.dragState.width,
                this.dragState.height
            )

            if (this.dragState.type === 'panel') {
                this.panelPosition = position
            } else {
                this.entryPosition = position
            }
        },
        finishDrag() {
            if (this.dragState && this.dragState.type === 'entry' && this.dragState.moved) {
                this.suppressEntryClick = true
            }
            this.dragState = null
            this.removeDragListeners()
        },
        removeDragListeners() {
            document.removeEventListener('mousemove', this.moveDrag)
            document.removeEventListener('mouseup', this.finishDrag)
            document.removeEventListener('touchmove', this.moveDrag)
            document.removeEventListener('touchend', this.finishDrag)
            document.removeEventListener('touchcancel', this.finishDrag)
        },
        getDragPoint(event) {
            const touch = event.touches && event.touches[0]
                ? event.touches[0]
                : event.changedTouches && event.changedTouches[0]
            if (touch) {
                return { x: touch.clientX, y: touch.clientY }
            }
            if (event.clientX === undefined || event.clientY === undefined) return null
            return { x: event.clientX, y: event.clientY }
        },
        clampFloatingPosition(left, top, width, height) {
            const margin = 8
            const viewportWidth = window.innerWidth || document.documentElement.clientWidth || width
            const viewportHeight = window.innerHeight || document.documentElement.clientHeight || height
            const maxLeft = Math.max(margin, viewportWidth - width - margin)
            const maxTop = Math.max(margin, viewportHeight - height - margin)

            return {
                left: Math.min(Math.max(left, margin), maxLeft),
                top: Math.min(Math.max(top, margin), maxTop)
            }
        },
        clampFloatingPositions() {
            if (this.entryPosition && this.$refs.entry) {
                const rect = this.$refs.entry.getBoundingClientRect()
                this.entryPosition = this.clampFloatingPosition(rect.left, rect.top, rect.width, rect.height)
            }
            if (this.panelPosition && this.$refs.panel) {
                const rect = this.$refs.panel.getBoundingClientRect()
                this.panelPosition = this.clampFloatingPosition(rect.left, rect.top, rect.width, rect.height)
            }
        },
        handleResize() {
            this.clampFloatingPositions()
            this.updatePosition()
        },
        updatePosition() {
            if (!this.active || !this.currentStep) return
            const target = this.getTarget(this.currentStep.selector)
            if (!target) {
                this.targetRect = null
                return
            }
            target.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' })
            window.setTimeout(() => {
                const rect = target.getBoundingClientRect()
                this.targetRect = {
                    top: rect.top,
                    left: rect.left,
                    right: rect.right,
                    bottom: rect.bottom,
                    width: rect.width,
                    height: rect.height
                }
            }, 180)
        },
        refreshVisibleSteps() {
            this.domTick += 1
            const count = this.steps.filter(step => this.getTarget(step.selector)).length
            if (this.currentIndex >= count) {
                this.currentIndex = Math.max(count - 1, 0)
            }
        },
        getTarget(selector) {
            const targets = Array.from(document.querySelectorAll(selector))
            return targets.find(target => {
                const rect = target.getBoundingClientRect()
                const style = window.getComputedStyle(target)
                return rect.width > 0
                    && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden'
            }) || null
        }
    }
}
</script>

<style lang="scss" scoped>
.sales_guide__entry {
    width: 100%;
    min-height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
    padding: 10px 12px;
    border: 1px solid #c9d8e8;
    border-radius: 8px;
    background: #f6fbff;
    color: #183b5f;
    text-align: left;
    cursor: pointer;
}

.sales_guide--floating .sales_guide__entry {
    position: fixed;
    right: 18px;
    bottom: 18px;
    z-index: 2100;
    width: 244px;
    margin: 0;
    box-shadow: 0 12px 34px rgba(16, 24, 40, .18);
    cursor: grab;
    user-select: none;
    touch-action: none;
}

.sales_guide--floating .sales_guide__entry:active {
    cursor: grabbing;
}

.sales_guide__entry b,
.sales_guide__entry em {
    display: block;
}

.sales_guide__entry b {
    font-size: 13px;
    font-weight: 600;
}

.sales_guide__entry em {
    margin-top: 2px;
    font-size: 12px;
    font-style: normal;
    color: #5d7893;
}

.sales_guide__entry i {
    font-size: 18px;
    color: #1d65a6;
}

.sales_guide__mask {
    position: fixed;
    inset: 0;
    z-index: 2990;
    background: rgba(17, 24, 39, .48);
}

.sales_guide__spot {
    position: fixed;
    z-index: 2991;
    border: 2px solid #4da3ff;
    border-radius: 10px;
    box-shadow: 0 0 0 9999px rgba(17, 24, 39, .28), 0 10px 35px rgba(13, 71, 125, .35);
    pointer-events: none;
    transition: all .18s ease;
}

.sales_guide__panel {
    position: fixed;
    z-index: 2992;
    max-height: calc(100vh - 16px);
    overflow-y: auto;
    padding: 14px;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 18px 55px rgba(15, 23, 42, .26);
}

.sales_guide__points {
    display: grid;
    gap: 6px;
    margin: 10px 0 0;
    padding: 0;
    list-style: none;
}

.sales_guide__points li {
    position: relative;
    padding-left: 14px;
    font-size: 12px;
    line-height: 1.35;
    color: #475467;
}

.sales_guide__points li::before {
    content: "";
    position: absolute;
    left: 0;
    top: .55em;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #1d65a6;
}

.sales_guide__progress,
.sales_guide__actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.sales_guide__progress {
    margin-bottom: 8px;
    font-size: 11px;
    color: #667085;
    cursor: grab;
    user-select: none;
    touch-action: none;
}

.sales_guide__progress:active {
    cursor: grabbing;
}

.sales_guide__progress button,
.sales_guide__actions button {
    border: 0;
    background: transparent;
    color: #667085;
    cursor: pointer;
}

.sales_guide__panel h2 {
    margin: 0 0 6px;
    font-size: 16px;
    line-height: 1.25;
    font-weight: 600;
    color: #101828;
}

.sales_guide__panel p {
    margin: 0;
    font-size: 13px;
    line-height: 1.45;
    color: #344054;
}

.sales_guide__hint {
    margin-top: 10px;
    padding: 9px 10px;
    border-radius: 7px;
    background: #f2f7fb;
    color: #275070;
    font-size: 12px;
    line-height: 1.35;
}

.sales_guide__dots {
    display: flex;
    gap: 5px;
    margin: 12px 0;
}

.sales_guide__dots span {
    width: 21px;
    height: 3px;
    border-radius: 999px;
    background: #d0d5dd;
}

.sales_guide__dots span.active {
    background: #1d65a6;
}

.sales_guide__actions button {
    min-height: 30px;
    padding: 0 10px;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    background: #fff;
    color: #344054;
}

.sales_guide__actions button:disabled {
    opacity: .45;
    cursor: default;
}

.sales_guide__actions .sales_guide__primary {
    border-color: #1d65a6;
    background: #1d65a6;
    color: #fff;
}
</style>
