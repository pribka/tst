from common.page_config.base_model.pages import BaseModelPage, BaseModelMetaConfig, BaseModelPageConfig
from .forms import BaseDocumentFormInfo


class BaseDocumentPage(BaseModelPage):
    meta = BaseModelMetaConfig(
        page_config=BaseModelPageConfig(
            form_info=BaseDocumentFormInfo(
            )
        )
    )
