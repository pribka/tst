# Закомментил для оптимизации
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from django.db.transaction import on_commit
#
# from django_q.tasks import async_task
#
# from common.catalogs.models import GoodsModel
#
# from .models import TPGoodsOrderModel, GoodsOrderModel
# from .utils import update_order_index

#
# @receiver(post_save, sender=GoodsModel)
# def index_order_because_goods(sender, instance, created, raw, using, update_fields, **kwargs):
#     if not created:
#         tp_goodsorders = instance.tp_goodsorders.all().prefetch_related('owner')
#         for tp_goodsorder in tp_goodsorders:
#             order = getattr(tp_goodsorder, 'owner', None)
#             if order:
#                 on_commit(lambda: async_task(update_order_index, order))
#

# @receiver(post_save, sender=TPGoodsOrderModel)
# def index_order_because_update_tpgoodsordermodel(sender, instance, created, raw, using, update_fields, **kwargs):
#     order = instance.owner
#     if order:
#         on_commit(lambda: async_task(update_order_index, order))
#
#
# @receiver(post_delete, sender=TPGoodsOrderModel)
# def index_order_because_delete_tp_goodsordermodel(sender, instance, **kwargs):
#     order = instance.owner
#     if order:
#         on_commit(lambda: async_task(update_order_index, order))
