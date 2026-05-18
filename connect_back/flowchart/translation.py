from modeltranslation.translator import translator, TranslationOptions
from .models import FlowchartModel

class FlowchartModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(FlowchartModel, FlowchartModelTranslationOptions)



