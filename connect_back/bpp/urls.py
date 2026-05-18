from rest_framework.routers import DefaultRouter
from . import views

app_name = 'bpp'

router = DefaultRouter()
router.register(r'edition', views.EditionViewSet, basename='edition')
router.register(r'edition_part', views.EditionPartViewSet, basename='edition_part')
router.register(r'edition_unit', views.EditionUnitViewSet, basename='edition_unit')
router.register(r'incoming_invoice', views.IncomingInvoiceViewSet, basename='incoming_invoice')
router.register(r'act_write_off', views.ActWriteOffViewSet, basename='act_write_off')
router.register(r'transfer', views.EditionUnitTransferViewSet, basename='transfer')
router.register(r'edition_author', views.EditionAuthorViewSet, basename='edition_author')
router.register(r'edition_publisher', views.EditionPublisherViewSet, basename='edition_publisher')
urlpatterns = router.urls
