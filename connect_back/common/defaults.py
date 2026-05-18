DEFAULT_ROUTES = {
    "dashboard": {
        "path": "dashboard",
        "pageWidget": "Front",
        "title": "Рабочий стол",
        "icon": "fi-rr-computer",
        "isFooter": False,
        "mobileOrder": 0,
        "descOrder": 0,
        "isShow": True
    },
    "meetings": {
        "pageWidget": "Meetings",
        "title": "Собрания",
        "isFooter": False,
        "icon": "fi-rr-video-camera",
        "mobileOrder": 1,
        "descOrder": 1,
        "isShow": True
    },
    "calendar": {
        "pageWidget": "Calendar",
        "title": "Календарь",
        "icon": "fi-rr-calendar-lines",
        "isFooter": True,
        "mobileOrder": 2,
        "descOrder": 2,
        "isShow": True
    },
    "my-bases": {
        "pageWidget": "MyBases",
        "title": "Мои базы",
        "icon": "fi-rr-hdd",
        "isFooter": False,
        "mobileOrder": 3,
        "descOrder": 3,
        "isShow": True
    },
    "team": {
        "pageWidget": "Team",
        "title": "Структура",
        "icon": "fi-rr-users",
        "isFooter": False,
        "mobileOrder": 4,
        "descOrder": 4,
        "isShow": True
    },
    "chat": {
        "pageWidget": "Chat",
        "title": "Чат",
        "icon": "fi-rr-comment",
        "isFooter": True,
        "mobileOrder": 5,
        "descOrder": 5
    },
    "tasks": {
        "pageWidget": "Tasks",
        "title": "Задачи",
        "icon": "fi-rr-list-check",
        "isFooter": True,
        "mobileOrder": 6,
        "descOrder": 6,
        "isShow": True
    },
    "tasks-kanban": {
        "descOrder": 0,
        "icon": "fi-rr-diagram-cells",
        "isFooter": False,
        "isShow": True,
        "mobileOrder": 0,
        "pageWidget": "PageKanban",
        "title": "Канбан"},
    "sprint": {
        "descOrder": 0,
        "icon": "fi-rr-diagram-cells",
        "isFooter": False,
        "isShow": True,
        "mobileOrder": 0,
        "pageWidget": "PageSprint",
        "title": "Спринты",
    },
    "groups": {
        "pageWidget": "groups",
        "title": "Команды",
        "icon": "fi-rr-users-alt",
        "isFooter": False,
        "mobileOrder": 7,
        "descOrder": 7,
        "isShow": True
    },
    "projects": {
        "pageWidget": "projects",
        "title": "Проекты",
        "icon": "fi-rr-money-check",
        "isFooter": False,
        "mobileOrder": 8,
        "descOrder": 8,
        "isShow": True
    },
    "files": {
        "pageWidget": "Files",
        "title": "Мои файлы",
        "icon": "fi-rr-document",
        "isFooter": False,
        "mobileOrder": 9,
        "descOrder": 9,
        "isShow": True
    },
    "helpdesk": {
        "pageWidget": "PageTask",
        "title": "Helpdesk",
        "icon": "fi-rr-cloud-question",
        "isFooter": False,
        "mobileOrder": 10,
        "descOrder": 10
    },
    "documents": {
        "pageWidget": "Documents",
        "title": "Документы",
        "icon": "fi-rr-template",
        "isFooter": False,
        "mobileOrder": 11,
        "descOrder": 11,
        "isShow": True
    },
    "contractors": {
        "pageWidget": "Contractors",
        "title": "Клиенты",
        "icon": "fi-rr-id-card-clip-alt",
        "isFooter": False,
        "mobileOrder": 12,
        "descOrder": 12,
        "isShow": True
    },
    "logistic": {
        "pageWidget": "PageTask",
        "title": "Логистика",
        "icon": "fi-rr-marker",
        "isFooter": False,
        "mobileOrder": 13,
        "descOrder": 13
    },
    "logistic-monitor": {
        "pageWidget": "LogisticMonitor",
        "title": "Монитор логиста",
        "icon": "fi-rr-route",
        "isFooter": False,
        "mobileOrder": 14,
        "descOrder": 14,
        "isShow": True
    },
    "goods": {
        "pageWidget": "ProductCatalog",
        "title": "Товары",
        "icon": "fi-rr-shop",
        "isFooter": False,
        "mobileOrder": 15,
        "descOrder": 15,
        "isShow": True
    },
    "orders": {
        "pageWidget": "Orders",
        "title": "Заказы",
        "icon": "fi-rr-shopping-bag",
        "isFooter": False,
        "mobileOrder": 16,
        "descOrder": 16,
        "isShow": True
    },
    "deals": {
        "pageWidget": "Deals",
        "title": "Сделки / контракты",
        "icon": "fi-rr-handshake",
        "isFooter": False,
        "mobileOrder": 17,
        "descOrder": 17,
        # Temporary hide until Deals module is ready for production rollout.
        "isShow": True
    },
    "interest": {
        "pageWidget": "PageTask",
        "title": "Интересы",
        "icon": "fi-rr-memo-circle-check",
        "isFooter": False,
        "mobileOrder": 17,
        "descOrder": 17,
        "isShow": True
    },
    "interest-kanban": {
        "pageWidget": "PageKanban",
        "title": "Интересы Канбан",
        "icon": "fi-rr-memo-circle-check",
        "isFooter": False,
        "mobileOrder": 18,
        "descOrder": 18,
        "isShow": True
    },
    "geoviewer": {
        "pageWidget": "GeoViewer",
        "title": "Карта задач",
        "icon": "fi-rr-map-marker",
        "isFooter": False,
        "mobileOrder": 19,
        "descOrder": 19,
        "isShow": True
    }
}

DEFAULT_ROUTES_META = {
  "tasks": {
    "title": "Задачи",
    "task_type": "task",
    "name": "tasks",
    "pageWidget": "Tasks",
    "pageActions": {
      "add": True,
      "help": True
    }
  },
  "meetings": {
    "title": "Собрания",
    "name": "meetings",
    "pageWidget": "Meetings",
    "pageActions": {
      "add": True,
      "help": True
    }
  },
  "calendar": {
    "title": "Календарь",
    "name": "calendar",
    "pageWidget": "Calendar",
    "pageActions": {
      "add": True,
      "help": True
    }
  },
  "dashboard": {
    "title": "Рабочий стол",
    "name": "dashboard",
    "pageWidget": "Front",
    "pageActions": {
      "help": True
    }
  },
  "chat": {
    "title": "Чат",
    "name": "chat",
    "pageWidget": "Chat",
    "pageActions": {
      "help": True
    }
  },
  "interest": {
    "title": "Интересы",
    "name": "interest",
    "pageWidget": "PageTask",
    "task_type": "interest",
    "buttonConfig": {
      "label": "Добавить интерес"
    },
    "pageActions": {
      "add": True,
      "help": True
    }
  },
  "interest-kanban": {
    "title": "Интересы Канбан",
    "name": "interest-kanban",
    "pageWidget": "PageKanban",
    "task_type": "interest",
    "buttonConfig": {
      "label": "Добавить интерес"
    },
    "pageActions": {
      "add": True,
      "help": True
    }
  },
  "logistic": {
    "title": "Логистика",
    "name": "logistic",
    "pageWidget": "PageTask",
    "task_type": "logistic",
    "pageActions": {
      "help": True
    }
  },
  "my-bases": {
    "title": "Мои базы",
    "name": "my-bases",
    "pageWidget": "MyBases",
    "pageActions": {
      "help": True
    }
  },
  "team": {
    "title": "Структура",
    "name": "team",
    "pageWidget": "Team",
    "pageActions": {
      "help": True
    }
  },
  "tasks-kanban": {
    "title": "Канбан",
    "name": "tasks-kanban",
    "pageWidget": "PageKanban",
    "pageActions": {
      "add": True,
      "help": True
    }
  },
  "sprint": {
    "title": "Спринты",
    "name": "sprint",
    "pageWidget": "PageSprint",
    "pageActions": {
      "help": True
    }
  },
  "files": {
    "title": "Мои файлы",
    "name": "files",
    "pageWidget": "Files",
    "pageActions": {
      "help": True
    }
  },
  "groups": {
    "title": "Команды",
    "name": "groups",
    "pageWidget": "groups",
    "pageActions": {
      "help": True,
      "add": True
    }
  },
  "projects": {
    "title": "Проекты",
    "name": "projects",
    "pageWidget": "projects",
    "pageActions": {
      "help": True,
      "add": True
    }
  },
  "orders": {
    "title": "Заказы",
    "name": "orders",
    "pageWidget": "Orders",
    "buttonConfig": {
      "label": "Оформить заказ"
    },
    "pageActions": {
      "help": True,
      "add": True
    }
  },
  "deals": {
    "title": "Сделки / контракты",
    "name": "deals",
    "pageWidget": "Deals",
    "pageActions": {
      "help": True,
      "add": True
    }
  }
}

