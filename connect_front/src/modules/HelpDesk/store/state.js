export default () => ({
    statusList: {},
    statusLoader: false,
    workTimeSettings:  {
        tableInfo:[
            {
                "field": "work_type",
                "headerName": "Тип работы"
            },
            {
                "field": "description",
                "headerName": "Описание",
                "class": "desc"
            },
            {
                "field": "is_result",
                "headerName": "Не брать в зачет"
            },
            {
                "field": "author",
                "headerName": "Автор"
            },
            {
                "field": "duration",
                "headerName": "Потрачено",
                "class": "duration"
            },
            {
                "field": "measure_unit",
                "headerName": "Единица измерения"
            },
            {
                "field": "date",
                "headerName": "Дата",
                "class": "hours"
            },
            {
                "field": "actions",
                "headerName": "",
                "class": "action"
            }
        ]
    }

})