import { getEmptyTemplate } from './templateFactory';

export default {
    reportModalVisible: false,
    reportModalVisibleCheck: false,
    createAggregateFieldVisible: false,
    activeTemplate: getEmptyTemplate(),
    originalTemplate: null, // Для хранения исходного состояния шаблона
    reportCategories: [],
    infiniteId: {
        'templates': new Date(),
        'my_templates': new Date()
    },
    templates: {
        'templates': {
            results: []
        },
        'my_templates': {
            results: []
        },
    }
}
