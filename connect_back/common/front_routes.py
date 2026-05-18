from django.utils.translation import gettext_lazy as _, pgettext_lazy

import common.catalogs.models
from common.current_profile.middleware import get_current_authenticated_profile

from staff import front_routes as staff_routes
from bpp import front_routes as bpp_routes

try:
    from bkz3.settings import FRONT_CATEGORIES
except ImportError:
    FRONT_CATEGORIES = {'dashboard': (),
                        'communication': (
                            'meetings', 'chat', 'tasks', 'groups', 'projects', 'business_processes', 'files'
                        ), }

from bkz3.settings import MOBILE_FRONT_CATEGORIES

try:
    from bkz3.settings import MOBILE_APP_FRONT_CATEGORIES
except ImportError:
    MOBILE_APP_FRONT_CATEGORIES = ('tasks', 'logistic', 'chat', 'projects',)

from . import page_config
from . import models
from bpp.models import EditionModel

from flowchart.models import FlowchartModel


class FileCategory(page_config.Category):
    name = 'files'
    path = 'files'
    title = _('Files')
    icon = 'appstore'
    children = page_config.SetConfig(
        files=page_config.BaseModelPage(model=models.File, icon='file'),
        instances=('files',),
    )

    def prepare_files(self):
        self.children.files.meta.page_config.form_info.actions.create = page_config.BaseModelAction(
            content_type='multipart/form-data',
            path=models.File.get_data_path()
        )


class FrontPage(page_config.BaseConfig):
    name = 'dashboard'
    path = 'dashboard'
    icon = 'desktop'
    icon_supplier = 'ant'
    menu_widget = 'ListWidget'
    nav_widget = 'NavPage'
    title = _('Desktop')
    show_menu = True
    page_widget = 'Front'
    is_page = True

    def get_dict(self):
        data = {
            'name': self.name,
            'path': self.path,
            'meta': {
                'icon': self.icon,
                'iconSupplier': self.icon_supplier,
                'menuWidget': self.menu_widget,
                'navWidget': self.nav_widget,
                'title': self.title,
                'showMenu': self.show_menu,
                'pageWidget': self.page_widget,
                'isPage': self.is_page
            }
        }
        return data


class TestPage(page_config.Category):
    name = 'test_page'
    path = 'test_page'
    icon = 'desktop'
    title = 'Тестовая группа'
    children = page_config.SetConfig(
        edition=page_config.BaseModelPage(model=EditionModel, icon='cluster'),
        instances=FRONT_CATEGORIES.get('test_page', ())

    )

    def prepare_edition(self):
        self.children.edition.meta.drawer_mode = True


from bkz3.settings import GROUP_LABEL_IN_MENU

class CommunicationCategory(page_config.Category):
    name = 'communication'
    path = 'communication'
    title = _('Communication')
    icon = 'share-alt'

    if GROUP_LABEL_IN_MENU == 'GROUPS':
        group_title = _('Groups')
    else:
        group_title = GROUP_LABEL_IN_MENU

    children = page_config.SetConfig(
        team=page_config.BaseEmbeddedPage(
            name='team',
            path='team',
            icon='team',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Team',
                favorite_support=False,
                is_page=True,
                title='Структура'
            )
        ),
        meetings=page_config.BaseEmbeddedPage(
            name='meetings',
            path='meetings',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Meetings',
                title=_('Meetings'),
            ),
            icon='video-camera',
        ),
        chat=page_config.BaseEmbeddedPage(
            name='chat',
            path='chat',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Chat',
                title=_('Chat'),
                badge_counter=True,
            ),
            icon='message',
        ),
        tasks=page_config.BaseEmbeddedPage(
            name='tasks',
            path='Tasks',
            page_redirect='tasks-list-page',
            children_type='import',
            children_config='task',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Tasks',
                title=_('Tasks'),
                extra={
                    "task_type": "task",
                    "pageConfig": {
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "fastCreate": True,
                                "size": "large",
                                "type": "primary",
                                "title": "Добавить задачу",
                                "icon": "plus",
                                "task_type": "task",
                            }
                        },
                        "showFilter": True
                    }
                }
            ),
            icon='profile'
        ),
        groups=page_config.BaseEmbeddedPage(
            name='groups',
            path='Groups',
            meta=page_config.BaseMetaPageConfig(
                page_widget='groups',
                title=group_title,  # ВРЕМЯНКА ДЛЯ ПРОМСИТЕХА
                background_color='#f6f7f9',
                extra={
                    'pageConfig': {
                        "showFilter": True
                    }
                }
            ),
            icon='team',
        ),
        projects=page_config.BaseEmbeddedPage(
            name='projects',
            path='Projects',
            meta=page_config.BaseMetaPageConfig(
                page_widget='projects',
                title=_('Projects'),
                background_color='#f6f7f9',
                extra={
                    'pageConfig': {
                        'showFilter': True,
                    }
                }
            ),
            icon='project',
        ),
        business_processes=page_config.BaseEmbeddedPage(
            name='business_processes',
            path='BusinessProcesses',
            children_type='import',
            children_config='businessProcesses',
            children_config_path='@apps/BusinessProcesses/config/router.js',
            page_redirect='',
            meta=page_config.BaseMetaPageConfig(
                page_widget='BusinessProcesses',
                title=_('Business processes'),
                background_color='#f6f7f9',
            ),
            icon='sync',
        ),

        flowchart=page_config.BaseEmbeddedPage(
            name='flowcharts',
            path='Flowcharts',
            meta=page_config.BaseMetaPageConfig(
                page_widget='flowchart',
                title='Блок-схемы',
                background_color='#f6f7f9',
                extra={
                    'showFooterMenu': False,
                }
            ),
            icon='cluster', ),
        files=page_config.BaseEmbeddedPage(
            name='files',
            path='files',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Files',
                title=_("My files"),
                background_color='#fff',
            ),
            icon='folder',
        ),
        helpdesk=page_config.BaseEmbeddedPage(
            name='helpdesk',
            path='helpdesk',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageTask',
                title=_('Helpdesk'),
                extra={
                    'task_type': 'helpdesk',
                    'pageConfig': {
                        "showFilter": True,
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "fastCreate": True,
                                "size": "large",
                                "type": "primary",
                                "title": _('Add ticket'),
                                "icon": "plus",
                                "task_type": "helpdesk"
                            }
                        },
                    },

                },
            ),

            icon='file-done',
        ),
        my_bases=page_config.BaseEmbeddedPage(
            name='my_bases',
            path='my_bases',
            meta=page_config.BaseMetaPageConfig(
                page_widget='MyBases',
                title="Мои базы",
                extra={
                    'pageConfig': {
                        'showFilter': True,
                    }
                }
            ),
            icon='database',
        ),
        calendar=page_config.BaseEmbeddedPage(
            name='calendar',
            path='calendar',
            icon='calendar',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Calendar',
                title='Календарь',
            )
        ),
        instances=FRONT_CATEGORIES.get('communication', ())
    )

    def prepare_children(self):
        if get_current_authenticated_profile().can_create_workgroups:
            self.children.groups.meta.extra = {
                    "pageConfig": {
                        "headerButtons": {
                            "createButton": {
                                "size": "large",
                                "type": "primary",
                                "title": "Добавить команду",
                                "icon": "plus",
                            }
                        },
                        "showFilter": True
                    }
                }
            self.children.projects.meta.extra = {
                "pageConfig": {
                    "headerButtons": {
                        "createButton": {
                            "size": "large",
                            "type": "primary",
                            "title": "Добавить проект",
                            "icon": "plus",
                        }
                    },
                    "showFilter": True
                }
            }
        return


class CommonCategory(page_config.Category):
    name = 'common'
    path = 'common'
    title = _('Common')
    icon = 'cluster'
    children = page_config.SetConfig(
        individuals=page_config.BaseModelPage(model=models.Individual),
        organizations=page_config.BaseModelPage(model=models.Organization),
        warehouses=page_config.BaseModelPage(model=common.catalogs.models.WarehouseModel),
        plan_of_characteristic=page_config.BaseModelPage(model=models.PlanOfCharacteristic),
        instances=('individuals', 'organizations', 'warehouses', 'plan_of_characteristic')
    )


class BusinessProcessesCategory(page_config.Category):
    name = 'business_processes'
    path = 'business_processes'
    title = _('Business processes')
    icon = 'sync'


class CRMCategory(page_config.Category):
    name = 'crm'
    path = 'crm'
    title = _('CRM')
    icon = ''
    children = page_config.SetConfig(
        logistic=page_config.BaseEmbeddedPage(
            name='logistic',
            path='logistic',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageTask',
                title='Логистика',
                extra={'task_type': 'logistic', 'pageConfig': {
                    "headerButtons": None,
                    "showFilter": True,
                }
                       },
            ),
            icon='environment',
        ),
        logistic_monitor=page_config.BaseEmbeddedPage(
            name='logistic_monitor',
            path='logistic-monitor',
            meta=page_config.BaseMetaPageConfig(
                page_widget='LogisticMonitor',
                title='Монитор логиста',
            ),
            icon='schedule',
        ),
        goods=page_config.BaseEmbeddedPage(
            name='goods',
            path='goods',
            meta=page_config.BaseMetaPageConfig(
                page_widget='ProductCatalog',
                title=pgettext_lazy('plural', 'Goods'),
                badge_counter=False,
            ),
            icon='shop',
        ),
        orders=page_config.BaseEmbeddedPage(
            name='orders',
            path='orders',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Orders',
                title=_('Orders'),
                badge_counter=False,
                extra={
                    'pageConfig': {
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "size": "large",
                                "type": "primary",
                                "title": "Создать заказ",
                                "icon": "plus",
                            }
                        },
                    },

                }
            ),
            icon='shopping',
        ),
        deals=page_config.BaseEmbeddedPage(
            name='deals',
            path='deals',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Deals',
                title=_('Сделки / контракты'),
                extra={
                    'pageConfig': {
                        "showFilter": True,
                    }
                },
            ),
            icon='fi-rr-handshake',
        ),
        documents=page_config.BaseEmbeddedPage(
            name='documents',
            path='documents',
            meta=page_config.BaseMetaPageConfig(
                title='Документы',
                page_widget='Documents'
            ),
            icon='fi-rr-template'
        ),
        consolidation=page_config.BaseEmbeddedPage(
            name='consolidation',
            path='consolidation',
            meta=page_config.BaseMetaPageConfig(
                title='Консолидация',
                page_widget='Сonsolidation'
            ),
            icon='fi-rr-sitemap'
        ),
        interest=page_config.BaseEmbeddedPage(
            name='interest',
            path='interest',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageTask',
                title='Интересы',
                extra={
                    'task_type': 'interest',
                    'pageConfig': {
                        "showFilter": True,
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "fastCreate": False,
                                "size": "large",
                                "type": "primary",
                                "title": "Добавить интерес",
                                "icon": "plus",
                                "task_type": "interest",
                            }
                        },
                    }
                },
            ),
            icon='file-done',
        ),
        interest_kanban=page_config.BaseEmbeddedPage(
            name='interest_kanban',
            path='interest_kanban',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageKanban',
                title='Интересы Канбан',
                extra={'task_type': 'interest', 'pageConfig': {"showFilter": True}},
            ),
            icon='database',
        ),
        logistic_kanban=page_config.BaseEmbeddedPage(
            name='logistic-kanban',
            path='logistic-kanban',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageKanban',
                title='Канбан логистики',
                extra={'task_type': 'logistic', 'pageConfig': {"showFilter": True}},
            ),
            icon='database',
        ),
        geoviewer=page_config.BaseEmbeddedPage(
            name='geoviewer',
            path='geoviewer',
            meta=page_config.BaseMetaPageConfig(
                page_widget='GeoViewer',
                title='Карта задач',
            ),
            icon='environment',
        ),
        contractors=page_config.BaseEmbeddedPage(
            name='contractors',
            path='contractors',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Contractors',
                title='Клиенты',
            ),
            icon='team',
        ),
        instances=tuple(dict.fromkeys((*FRONT_CATEGORIES.get('crm', ()), 'deals')))
    )

    def prepare_children(self):
        if get_current_authenticated_profile().is_storekeeper:
            self.children.orders.meta.extra = {
                "pageConfig": {
                    "headerButtons": None,
                    "showFilter": True
                }
            }

class Routes(page_config.SetConfig):
    """Главный класс с роутами."""
    dashboard = FrontPage()
    communication = CommunicationCategory()
    crm = CRMCategory()
    test_page = TestPage()
    files = FileCategory()
    staff = staff_routes.StaffCategory()
    instances = tuple(key for key, value in FRONT_CATEGORIES.items())


class AltRoutes(page_config.SetConfig):
    """Альтернативные роуты (без категорий)."""
    dashboard = FrontPage()
    meetings = page_config.BaseEmbeddedPage(
            name='meetings',
            path='meetings',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Meetings',
                title=_('Meetings'),
            ),
            icon='video-camera',
        )
    chat = page_config.BaseEmbeddedPage(
            name='chat',
            path='chat',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Chat',
                title=_('Chat'),
                badge_counter=True,
            ),
            icon='message',
        )
    tasks = page_config.BaseEmbeddedPage(
            name='tasks',
            path='Tasks',
            page_redirect='tasks-list-page',
            children_type='import',
            children_config='task',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Tasks',
                title=_('Tasks'),
                extra={
                    "task_type": "task",
                    "pageConfig": {
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "fastCreate": True,
                                "size": "large",
                                "type": "primary",
                                "title": "Добавить задачу",
                                "icon": "plus",
                                "task_type": "task",
                            }
                        },
                        "showFilter": True
                    }
                }
            ),
            icon='profile'
        )
    kanban = page_config.BaseEmbeddedPage()
    calendar = page_config.BaseEmbeddedPage()
    gantt = page_config.BaseEmbeddedPage()
    sprint = page_config.BaseEmbeddedPage()
    groups = page_config.BaseEmbeddedPage(
            name='groups',
            path='Groups',
            meta=page_config.BaseMetaPageConfig(
                page_widget='groups',
                title=_('Groups'),
                background_color='#f6f7f9'
            ),
            icon='team',
        )
    projects = page_config.BaseEmbeddedPage(
            name='projects',
            path='Projects',
            meta=page_config.BaseMetaPageConfig(
                page_widget='projects',
                title=_('Projects'),
                background_color='#f6f7f9'
            ),
            icon='project',
        )
    business_processes = page_config.BaseEmbeddedPage(
            name='business_processes',
            path='BusinessProcesses',
            children_type='import',
            children_config='businessProcesses',
            children_config_path='@apps/BusinessProcesses/config/router.js',
            page_redirect='',
            meta=page_config.BaseMetaPageConfig(
                page_widget='BusinessProcesses',
                title=_('Business processes'),
                background_color='#f6f7f9',
            ),
            icon='sync',
        )
    files = page_config.BaseEmbeddedPage(
            name='files',
            path='files',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Files',
                title=_("My files"),
                background_color='#fff',
            ),
            icon='folder',
        )
    helpdesk = page_config.BaseEmbeddedPage(
            name='helpdesk',
            path='helpdesk',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageTask',
                title=_('Helpdesk'),
                extra={
                    'task_type': 'helpdesk',
                    'pageConfig': {
                        "showFilter": True,
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "fastCreate": True,
                                "size": "large",
                                "type": "primary",
                                "title": _('Add ticket'),
                                "icon": "plus",
                                "task_type": "helpdesk"
                            }
                        },
                    },

                },
            ),

            icon='file-done',
        )

    logistic = page_config.BaseEmbeddedPage(
            name='logistic',
            path='logistic',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageTask',
                title='Логистика',
                extra={'task_type': 'logistic', 'pageConfig': {
                    "headerButtons": None,
                    "showFilter": True,
                }
                       },
            ),
            icon='environment',
        )
    logistic_monitor = page_config.BaseEmbeddedPage(
            name='logistic_monitor',
            path='logistic-monitor',
            meta=page_config.BaseMetaPageConfig(
                page_widget='LogisticMonitor',
                title='Монитор логиста',
            ),
            icon='schedule',
        )
    goods = page_config.BaseEmbeddedPage(
            name='goods',
            path='goods',
            meta=page_config.BaseMetaPageConfig(
                page_widget='ProductCatalog',
                title=pgettext_lazy('plural', 'Goods'),
                badge_counter=False,
            ),
            icon='shop',
        )
    orders = page_config.BaseEmbeddedPage(
            name='orders',
            path='orders',
            meta=page_config.BaseMetaPageConfig(
                page_widget='Orders',
                title=_('Orders'),
                badge_counter=False,
            ),
            icon='shopping',
        )
    interest = page_config.BaseEmbeddedPage(
            name='interest',
            path='interest',
            meta=page_config.BaseMetaPageConfig(
                page_widget='PageTask',
                title='Интересы',
                extra={'task_type': 'interest', 'pageConfig': {"showFilter": True}},
            ),
            icon='file-done',
        )
    test_page = TestPage()
    files_generated = FileCategory()
    staff = staff_routes.StaffCategory()


class MobileRoutes(page_config.SetConfig):
    dashboard = page_config.BaseEmbeddedPage(
        name='dashboard',
        path='dashboard',
        icon='desktop',
        meta=page_config.BaseMetaPageConfig(
            title="Рабочий стол",
            show_menu=True,
            page_widget="Front",
            is_page=True,
            extra={
                "showFooterMenu": MOBILE_FRONT_CATEGORIES.get('dashboard', dict()).get('show_footer_menu', False),
            }
        )
    )
    team = page_config.BaseEmbeddedPage(
        name='team',
        path='team',
        meta=page_config.BaseMetaPageConfig(
            title='Структура',
            page_widget='Team',
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('team', dict()).get('show_footer_menu', False),
            }
        ),
        icon='team',
    )
    mybases = page_config.BaseEmbeddedPage(
        name='mybases',
        path='mybases',
        meta=page_config.BaseMetaPageConfig(
            title='Мои базы',
            page_widget='MyBases',
            background_color='#f6f7f9',
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('mybases', dict()).get('show_footer_menu', False),
                'pageConfig': {'showFilter': True}
            }
            ),
        icon='database'
    )
    tasks = page_config.BaseEmbeddedPage(
        name='tasks',
        path='Tasks',
        meta=page_config.BaseMetaPageConfig(
            page_widget='PageTask',
            title=_('Tasks'),
            extra={
                "task_type": "task",
                "showFooterMenu": MOBILE_FRONT_CATEGORIES.get('tasks', dict()).get('show_footer_menu', False),
                "pageConfig": {
                    "headerButtons": {
                        "createButton": {
                            "show": True,
                            "fastCreate": False,
                            "size": "large",
                            "type": "primary",
                            "title": "Добавить задачу",
                            "icon": "plus",
                            "task_type": "task",
                        }
                    },
                    "showFilter": True
                }
            }
        ),
        icon='profile'
    )
    interest = page_config.BaseEmbeddedPage(
        name='interest',
        path='interest',
        meta=page_config.BaseMetaPageConfig(
            page_widget='PageTask',
            title='Интересы',
            extra={
                'task_type': 'interest',
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('interest', dict()).get('show_footer_menu', False),
                'pageConfig': {
                    'headerButtons': {
                        'createButton': {
                            'show': True,
                            'fastCreate': True,
                            'size': 'large',
                            'type': 'primary',
                            'title': 'Добавить интерес',
                            'icon': 'plus',
                            'task_type': 'interest'
                        }
                    },
                    'showFilter': True,
                }
            }
        ),
        icon='file-done'
    )
    calendar = page_config.BaseEmbeddedPage(
        name='calendar',
        path='calendar',
        meta=page_config.BaseMetaPageConfig(
            page_widget='Calendar',
            title='Календарь',
            extra={
                "showFooterMenu": MOBILE_FRONT_CATEGORIES.get('calendar', dict()).get('show_footer_menu', False),
            }
        ),
        icon='calendar',
    )
    sprints = page_config.BaseEmbeddedPage(
        name='sprints',
        path='Sprints',
        meta=page_config.BaseMetaPageConfig(
            page_widget='PageSprint',
            title='Спринты',
            extra={
                "showFooterMenu": MOBILE_FRONT_CATEGORIES.get('sprints', dict()).get('show_footer_menu', False),
                "pageConfig": {
                    "headerButtons": {
                        "createButton": {
                            "show": True,
                            "fastCreate": False,
                            "size": "large",
                            "type": "primary",
                            "title": "Создать спринт",
                            "icon": "plus",
                        }
                    },
                    "showFilter": True
                }
            }
        ),
        icon="retweet"
    )
    chat = page_config.BaseEmbeddedPage(
        name='chat',
        path='chat',
        page_redirect='',
        icon='message',
        meta=page_config.BaseMetaPageConfig(
            page_widget='Chat',
            title=_('Chat'),
            badge_counter=True,
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('chat', dict()).get('show_footer_menu', False),
            }
        )
    )
    meetings = page_config.BaseEmbeddedPage(
        name='meetings',
        path='meetings',
        meta=page_config.BaseMetaPageConfig(
            page_widget='Meetings',
            title=_('Meetings'),
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('meetings', dict()).get('show_footer_menu', False),
            }
        ),
        icon='video-camera',
    )
    groups = page_config.BaseEmbeddedPage(
        name='groups',
        path='Groups',
        meta=page_config.BaseMetaPageConfig(
            page_widget='groups',
            title="Команды",
            background_color='#f6f7f9',
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('groups', dict()).get('show_footer_menu', False),
            }
        ),
        icon='team',
    )
    projects = page_config.BaseEmbeddedPage(
        name='projects',
        path='Projects',
        meta=page_config.BaseMetaPageConfig(
            page_widget='projects',
            title=_('Projects'),
            background_color='#f6f7f9',
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('projects', dict()).get('show_footer_menu', False),
            }
        ),
        icon='project',
    )
    goods = page_config.BaseEmbeddedPage(
        name='goods',
        path='goods',
        meta=page_config.BaseMetaPageConfig(
            page_widget='ProductCatalog',
            title=pgettext_lazy('plural', 'Goods'),
            badge_counter=False,
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('goods', dict()).get('show_footer_menu', False),
            }
        ),
        icon='shop',
    )
    orders = page_config.BaseEmbeddedPage(
        name='orders',
        path='orders',
        meta=page_config.BaseMetaPageConfig(
            page_widget='Orders',
            title=_('Orders'),
            badge_counter=False,
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('orders', dict()).get('show_footer_menu', False),
            }
        ),
        icon='shopping',
    )
    logistic = page_config.BaseEmbeddedPage(
        name='logistic',
        path='logistic',
        meta=page_config.BaseMetaPageConfig(
            page_widget='PageTask',
            title='Логистика',
            extra={
                'task_type': 'logistic', 'pageConfig': {
                    "showFilter": True,
                },
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('logistic', dict()).get('show_footer_menu', False)
            },
        ),
        icon='environment',
    )
    contractors = page_config.BaseEmbeddedPage(
        name='contractors',
        path='contractors',
        meta=page_config.BaseMetaPageConfig(
            page_widget='Contractors',
            title='Клиенты',
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('contractors', dict()).get('show_footer_menu', False),
                'pageConfig': {'showFilter': True}
            }
        ),
        icon='team',
        is_page=True,
    )
    files = page_config.BaseEmbeddedPage(
        name='files',
        path='files',
        meta=page_config.BaseMetaPageConfig(
            page_widget='Files',
            title='Мои файлы',
            extra={
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('files', dict()).get('show_footer_menu', False),
            }
        ),
        icon='folder',
        is_page=True,
    )
    instances = tuple(key for key, value in MOBILE_FRONT_CATEGORIES.items())

    def get_dict(self):
        if get_current_authenticated_profile().can_create_workgroups:
            self.groups.meta.extra = {
                "showFooterMenu": MOBILE_FRONT_CATEGORIES.get('groups', dict()).get('show_footer_menu', False),
                "pageConfig": {
                        "headerButtons": {
                            "createButton": {
                                "show": True,
                                "fastCreate": False,
                                "size": "large",
                                "type": "primary",
                                "title": "Добавить команду",
                                "icon": "plus",
                            }
                        },
                        "showFilter": True
                    }
                }
            self.projects.meta.extra = {
                "showFooterMenu": MOBILE_FRONT_CATEGORIES.get('projects', dict()).get('show_footer_menu', False),
                "pageConfig": {
                    "headerButtons": {
                        "createButton": {
                            "show": True,
                            "fastCreate": False,
                            "size": "large",
                            "type": "primary",
                            "title": "Добавить проект",
                            "icon": "plus",
                        }
                    },
                    "showFilter": True
                }
            }
        if get_current_authenticated_profile().has_full_access_to_order_editing:
            self.orders.meta.extra = {
                'showFooterMenu': MOBILE_FRONT_CATEGORIES.get('orders', dict()).get('show_footer_menu', False),
                'pageConfig': {
                    "headerButtons": {
                        "createButton": {
                            "show": True,
                            "fastCreate": False,
                            "size": "large",
                            "type": "primary",
                            "title": "Создать заказ",
                            "icon": "plus",
                        }
                    },
                    "showFilter": True
                }
            }
        return super().get_dict()


class MobileAppRoutes(page_config.SetConfig):
    tasks = page_config.BaseMobileAppPage(
        name='Tasks',
        title='Задачи',
        component='Tasks',
        icon='fi-rr-list-check',
        options={
            'task_type': 'task',
            'show_create': False,
            'show_filter': False,
        },
    )
    logistic = page_config.BaseMobileAppPage(
        name='Logistic',
        title='Логистика',
        component='Tasks',
        icon='fi-rr-map-marker',
        options={
            'task_type': 'logistic',
            'show_create': False,
            'show_filter': True,
        },
    )
    home = page_config.BaseMobileAppPage(
        name='Home',
        title='Главная',
        component='Home',
        icon='fi-rr-home',
        options={
            'show_create': False,
            'show_search': False,
        },
    )
    projects = page_config.BaseMobileAppPage(
        name='Projects',
        title='Проекты',
        component='Projects',
        icon='fi-rr-money-check',
        options={
            'show_create': False,
            'show_filter': False,
        },
    )
    instances = MOBILE_APP_FRONT_CATEGORIES
