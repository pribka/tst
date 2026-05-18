export default {
    props: {

        // Модель (table.key)
        model: {
            type: String,
            required: true
        },
        transitionName: {
            type: String,
            default: 'zoom-big'
        },
        //Имя страницы где гаходиться модель (table.name)
        page_name: {
            type: String,
            required: true
        },
        placement: { // Расположение окна
            type: String,
            default: 'bottomLeft'
        },
        mode: { //tag, button
            type: String,
            default: 'tag'
        },
        size: { // Размер кнопки/поля фильтра
            type: String,
            default: ''
        },
        showSearch: { // По умолчанию текстовый поиск включен
            type: Boolean,
            default: true
        },

        scrollElements: { // Массив классов элементов, внутри которых будет прокручивать список к началу при выборе фильтра, по умолчанию прокручиваеться страница
            type: Array,
            default: () => []
        },

        queryParams: {  // Query параметры 
            type: Object,
            default: () => null
        },

        excludeFields: { // Исключить поля из рендеринга
            type: Array,
            default: () => []
        },
        width: {
            type: String,
            default: null
        },
        // Вертикальный вид фильтров
        vertical: {
            type: Boolean,
            default: () => false
        },
        // Скрыть кнопку сбросить фильтры
        hideResetBtn: {
            type: Boolean,
            default: () => false
        },
        //  Скрыть кнопку очистить фильтры
        hideClearBtn: {
            type: Boolean,
            default: () => false
        },
        // Что бы кнопки сьросить и очистить сразу начинали работать а не при нажатии на кнпоку поиск
        buttonsActive: {
            type: Boolean,
            default: () => false
        },
        zIndex: {
            type: Number,
            default: 1030
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        },
        onlySearch: {
            type: Boolean,
            default: false
        },
        align: {
            type: Object,
            default: () => {}
        },
        filterPrefix: {
            type: String,
            default: ''
        },
        modelLabel: {
            type: String,
            default: ''
        },
        injectSelectParams: {
            type: Object,
            default: () => {}
        },
        forceInit: {
            type: Boolean,
            default: false
        },
        popoverMaxWidth: {
            type: [Boolean,Number],
            default: false
        },
        initInputFocus: {
            type: Boolean,
            default: false
        },
        autoAdjustOverflow: {
            type: Boolean,
            default: false
        },
        filterButtonSize: {
            type: String,
            default: 'large'
        }
    },
}