# Stub data for AI message responses
STUB_INTENTS_DATA = [
    {
        "id": "d288ec90-979f-11f0-81dd-f98f0fe182e9",
        "created_at": "2025-09-22T13:35:13.643593+03:00",
        "intent_type": {
            "code": "create_task",
            "name": "Задача",
            "btn_title_create": "Создать задачу",
            "btn_title_open": "Открыть задачу",
            "btn_title_delete": "Удалить задачу",
            "metadata": {
                "backend_base_url": "/tasks/task/",
                "backend_base_url_full": "https://connect.gos24.kz/api/v1/tasks/task/",
                "get_parameter": "task",
                "target": {
                    "model": "tasks.TaskModel",
                    "action": "create"
                },
                "fixed_values": {
                    "task_type": "task"
                },
                "fields": {
                    "name": {
                        "type": "CharField",
                        "title": "Наименование",
                        "widget": "InputField",
                        "required": True
                    },
                    "description": {
                        "type": "TextField",
                        "title": "Описание",
                        "widget": "TextareaField",
                        "required": False
                    },
                    "operator": {
                        "type": "ForeignKey",
                        "model": "users.ProfileModel",
                        "title": "Ответственный",
                        "widget": "UserSelect",
                        "required": False
                    },
                    "date_start_plan": {
                        "type": "DateTimeField",
                        "title": "Дата начала",
                        "widget": "DateTimeField",
                        "required": False
                    },
                    "dead_line": {
                        "type": "DateTimeField",
                        "title": "Дата завершения",
                        "widget": "DateTimeField",
                        "required": False
                    },
                    "project": {
                        "type": "ForeignKey",
                        "model": "workgroups.WorkgroupModel",
                        "title": "Проект",
                        "widget": "ProjectSelect",
                        "required": False
                    },
                    "cooperators": {
                        "type": "ManyToManyField",
                        "model": "users.ProfileModel",
                        "title": "Соисполнители",
                        "widget": "UserSelect",
                        "required": False
                    },
                    "visors": {
                        "type": "ManyToManyField",
                        "model": "users.ProfileModel",
                        "title": "Наблюдатели",
                        "widget": "UserSelect",
                        "required": False
                    },
                    "workgroup": {
                        "type": "ForeignKey",
                        "model": "workgroups.WorkgroupModel",
                        "title": "Команда",
                        "widget": "GroupSelect",
                        "required": False
                    }
                }
            }
        },
        "resolutions": {
            "name": {
                "value": "Составление ТЗ",
                "status": "ready",
                "resolved": "Составление ТЗ",
                "candidates": []
            },
            "visors": {
                "value": [],
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "35112317-f2fe-11e8-80fd-305a3a75264b",
                        "repr": "Приб Константин",
                        "image": {
                            "id": "38c145ec-3fcd-11ed-9633-4216f3de51df",
                            "name": "-1756090511",
                            "path": "http://d.centersoft.kz:8000/media/avatars/38c145ec-3fcd-11ed-9633-4216f3de51df.jpg",
                            "size": 477388,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Константин"
                    },
                    {
                        "id": "d290c15e-6c07-11ee-98da-4216f3de51df",
                        "repr": "Приб Константин ОндреичGMAIL",
                        "image": None,
                        "for_name": "Константин"
                    }
                ]
            },
            "project": {
                "value": {
                    "id": "ad7e909c-82a0-11f0-a353-4216f3de51df",
                    "repr": "Проект для Мурада",
                    "image": None
                },
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "9c62fe9a-57dc-11f0-a5e9-4216f3de51df",
                        "repr": "Команда для Мурада",
                        "image": None,
                        "for_name": "Мурада"
                    },
                    {
                        "id": "ad7e909c-82a0-11f0-a353-4216f3de51df",
                        "repr": "Проект для Мурада",
                        "image": None,
                        "for_name": "Мурада"
                    }
                ]
            },
            "operator": {
                "value": {
                    "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                    "repr": "Сагитов ТагирЯндекс Наилевич",
                    "image": {
                        "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                        "name": "-900654706",
                        "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                        "size": 552299,
                        "is_image": True,
                        "extension": "jpg",
                        "content_type": "image/png"
                    }
                },
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                        "repr": "Сагитов ТагирЯндекс Наилевич",
                        "image": {
                            "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                            "name": "-900654706",
                            "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                            "size": 552299,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Тагир"
                    }
                ]
            },
            "dead_line": {
                "value": "2025-09-25T00:00:00",
                "status": "ready",
                "resolved": "2025-09-25T00:00:00",
                "candidates": []
            },
            "workgroup": {
                "value": {
                    "id": "9c62fe9a-57dc-11f0-a5e9-4216f3de51df",
                    "repr": "Команда для Мурада",
                    "image": None
                },
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "9c62fe9a-57dc-11f0-a5e9-4216f3de51df",
                        "repr": "Команда для Мурада",
                        "image": None,
                        "for_name": "Мурада"
                    },
                    {
                        "id": "ad7e909c-82a0-11f0-a353-4216f3de51df",
                        "repr": "Проект для Мурада",
                        "image": None,
                        "for_name": "Мурада"
                    }
                ]
            },
            "cooperators": {
                "value": [],
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "23968a2c-8a92-11ee-9f4a-4216f3de51df",
                        "repr": "Новый Акк Тагирович",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "4d294730-3d8f-11ee-9507-4216f3de51df",
                        "repr": "Сагитов Тагир Наилевич",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "8763ddfc-d49d-11ee-9f2e-4216f3de51df",
                        "repr": "Сагитов Тагир Наилевич",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                        "repr": "Сагитов ТагирЯндекс Наилевич",
                        "image": {
                            "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                            "name": "-900654706",
                            "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                            "size": 552299,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Тагир"
                    }
                ]
            },
            "description": {
                "value": "Составить ТЗ по делоклауду",
                "status": "ready",
                "resolved": "Составить ТЗ по делоклауду",
                "candidates": []
            },
            "date_start_plan": {
                "value": "2025-09-22T00:00:00",
                "status": "ready",
                "resolved": "2025-09-22T00:00:00",
                "candidates": []
            }
        },
        "status": "ready",
        "related_object": None
    },
    {
        "id": "8224ef7d-9788-11f0-81dd-f98f0fe182e9",
        "created_at": "2025-09-22T10:48:20.452891+03:00",
        "intent_type": {
            "code": "create_event",
            "name": "Событие",
            "btn_title_create": "Создать событие",
            "btn_title_open": "Открыть событие",
            "btn_title_delete": "Удалить событие",
            "metadata": {
                "backend_base_url": "/calendars/events/",
                "backend_base_url_full": "https://connect.gos24.kz/api/v1/calendars/events/",
                "get_parameter": "event",
                "target": {
                    "model": "event_calendar.EventCalendarModel",
                    "action": "create"
                },
                "fields": {
                    "name": {
                        "type": "CharField",
                        "title": "Название",
                        "widget": "InputField",
                        "required": True
                    },
                    "description": {
                        "type": "TextField",
                        "title": "Описание",
                        "widget": "TextareaField",
                        "required": False
                    },
                    "start_at": {
                        "type": "DateTimeField",
                        "title": "Дата начала",
                        "widget": "DateTimeField",
                        "required": True
                    },
                    "members": {
                        "type": "ManyToManyField",
                        "model": "users.ProfileModel",
                        "title": "Участники",
                        "widget": "UserSelect",
                        "required": False
                    }
                }
            }
        },
        "resolutions": {
            "name": {
                "value": "Событие",
                "status": "ready",
                "resolved": "Событие",
                "candidates": []
            },
            "members": {
                "value": [
                    {
                        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                        "repr": "Сагитов ТагирЯндекс Наилевич",
                        "image": {
                            "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                            "name": "-900654706",
                            "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                            "size": 552299,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        }
                    },
                    {
                        "id": "92820932-bcf7-11ef-890e-4216f3de51df",
                        "repr": "Ергалиева Дарига",
                        "image": {
                            "id": "2ae85d60-e9c7-11ef-ba38-4216f3de51df",
                            "name": "1928775529",
                            "path": "http://d.centersoft.kz:8000/media/avatars/2ae85d60-e9c7-11ef-ba38-4216f3de51df.jpg",
                            "size": 35566,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        }
                    }
                ],
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "23968a2c-8a92-11ee-9f4a-4216f3de51df",
                        "repr": "Новый Акк Тагирович",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "4d294730-3d8f-11ee-9507-4216f3de51df",
                        "repr": "Сагитов Тагир Наилевич",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "8763ddfc-d49d-11ee-9f2e-4216f3de51df",
                        "repr": "Сагитов Тагир Наилевич",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                        "repr": "Сагитов ТагирЯндекс Наилевич",
                        "image": {
                            "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                            "name": "-900654706",
                            "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                            "size": 552299,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Тагир"
                    },
                    {
                        "id": "92820932-bcf7-11ef-890e-4216f3de51df",
                        "repr": "Ергалиева Дарига",
                        "image": {
                            "id": "2ae85d60-e9c7-11ef-ba38-4216f3de51df",
                            "name": "1928775529",
                            "path": "http://d.centersoft.kz:8000/media/avatars/2ae85d60-e9c7-11ef-ba38-4216f3de51df.jpg",
                            "size": 35566,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Дарига"
                    },
                    {
                        "id": "a7745176-7e6f-11f0-8b37-4216f3de51df",
                        "repr": "ТЕст Дарига",
                        "image": None,
                        "for_name": "Дарига"
                    }
                ]
            },
            "start_at": {
                "value": "2025-09-24T12:00:00",
                "status": "ready",
                "resolved": "2025-09-24T12:00:00",
                "candidates": []
            },
            "description": {
                "value": None,
                "status": "optional",
                "resolved": None,
                "candidates": []
            }
        },
        "status": "ready",
        "related_object": None
    },
    {
        "id": "8224ef7e-9788-11f0-81dd-f98f0fe182e9",
        "created_at": "2025-09-22T10:48:20.503388+03:00",
        "intent_type": {
            "code": "create_meet",
            "name": "Видеовстреча",
            "btn_title_create": "Создать видеовстречу",
            "btn_title_open": "Открыть видеовстречу",
            "btn_title_delete": "Удалить видеовстречу",
            "metadata": {
                "backend_base_url": "/meetings/",
                "backend_base_url_full": "https://connect.gos24.kz/api/v1/meetings/",
                "get_parameter": "meeting",
                "target": {
                    "model": "meetings.PlannedMeetingModel",
                    "action": "create"
                },
                "fields": {
                    "name": {
                        "type": "CharField",
                        "title": "Название",
                        "widget": "InputField",
                        "required": True
                    },
                    "date_begin": {
                        "type": "DateTimeField",
                        "title": "Дата и время начала",
                        "widget": "DateTimeField",
                        "required": True
                    },
                    "members": {
                        "type": "ManyToManyField",
                        "model": "users.ProfileModel",
                        "title": "Участники",
                        "widget": "UserSelect",
                        "required": False
                    }
                }
            }
        },
        "resolutions": {
            "name": {
                "value": "Собрание",
                "status": "ready",
                "resolved": "Собрание",
                "candidates": []
            },
            "members": {
                "value": [
                    {
                        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                        "repr": "Сагитов ТагирЯндекс Наилевич",
                        "image": {
                            "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                            "name": "-900654706",
                            "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                            "size": 552299,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        }
                    }
                ],
                "status": "optional",
                "resolved": None,
                "candidates": [
                    {
                        "id": "23968a2c-8a92-11ee-9f4a-4216f3de51df",
                        "repr": "Новый Акк Тагирович",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "4d294730-3d8f-11ee-9507-4216f3de51df",
                        "repr": "Сагитов Тагир Наилевич",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "8763ddfc-d49d-11ee-9f2e-4216f3de51df",
                        "repr": "Сагитов Тагир Наилевич",
                        "image": None,
                        "for_name": "Тагир"
                    },
                    {
                        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
                        "repr": "Сагитов ТагирЯндекс Наилевич",
                        "image": {
                            "id": "67548d88-7f21-11f0-b44e-4216f3de51df",
                            "name": "-900654706",
                            "path": "http://d.centersoft.kz:8000/media/avatars/67548d88-7f21-11f0-b44e-4216f3de51df.jpg",
                            "size": 552299,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Тагир"
                    },
                    {
                        "id": "92820932-bcf7-11ef-890e-4216f3de51df",
                        "repr": "Ергалиева Дарига",
                        "image": {
                            "id": "2ae85d60-e9c7-11ef-ba38-4216f3de51df",
                            "name": "1928775529",
                            "path": "http://d.centersoft.kz:8000/media/avatars/2ae85d60-e9c7-11ef-ba38-4216f3de51df.jpg",
                            "size": 35566,
                            "is_image": True,
                            "extension": "jpg",
                            "content_type": "image/png"
                        },
                        "for_name": "Дарига"
                    },
                    {
                        "id": "a7745176-7e6f-11f0-8b37-4216f3de51df",
                        "repr": "ТЕст Дарига",
                        "image": None,
                        "for_name": "Дарига"
                    }
                ]
            },
            "date_begin": {
                "value": "2025-09-24T12:00:00",
                "status": "ready",
                "resolved": "2025-09-24T12:00:00",
                "candidates": []
            }
        },
        "status": "ready",
        "related_object": None
    }
]
