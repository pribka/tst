название таблицы cost_table

колонки:
[
    {
        "key": "name",
        "title": "Наименование",
        "width": 400,
        "sorter": true, - тут сам смотри будет сортировка или нет
        "hidable": true,
        "visible": true,
        "dataIndex": "name",
        "scopedSlots": {
            "customRender": "name"
        },
        "cellRenderer": "StringRow",
        "defaultTitle": "Наименование"
    },
    {
        "key": "article_number",
        "title": "Код товара",
        "width": 180,
        "sorter": true, - тут сам смотри будет сортировка или нет
        "hidable": true,
        "visible": true,
        "dataIndex": "article_number",
        "scopedSlots": {
            "customRender": "article_number"
        },
        "cellRenderer": "StringRow",
        "defaultTitle": "Код товара"
    },
    {
        "key": "quantity",
        "title": "Количество",
        "width": 180,
        "sorter": true, - тут сам смотри будет сортировка или нет
        "hidable": true,
        "visible": true,
        "dataIndex": "quantity",
        "scopedSlots": {
            "customRender": "quantity"
        },
        "cellRenderer": "StringRow",
        "defaultTitle": "Количество"
    }
]