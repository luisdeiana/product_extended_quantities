from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class PurchaseLine(metaclass=PoolMeta):
    __name__ = 'purchase.line'

    quantity_available = fields.Function(
        fields.Float('Stock', digits='unit', readonly=True),
        'on_change_with_quantity_available')
    forecast_quantity_available = fields.Function(
        fields.Float('Stock Previsto', digits='unit', readonly=True),
        'on_change_with_forecast_quantity_available')

    @fields.depends('product', 'type', 'warehouse', 'purchase', '_parent_purchase.warehouse')
    def on_change_with_quantity_available(self, name=None):
        return self._on_change_stock_value('quantity')

    @fields.depends('product', 'type', 'warehouse', 'purchase', '_parent_purchase.warehouse')
    def on_change_with_forecast_quantity_available(self, name=None):
        return self._on_change_stock_value('forecast_quantity')

    @fields.depends('product', 'type', 'warehouse', 'purchase', '_parent_purchase.warehouse')
    def _on_change_stock_value(self, quantity_name):
        if self.type != 'line' or not self.product:
            return 0.0

        Product = Pool().get('product.product')

        stock_context = Product._get_default_stock_context()
        if not stock_context:
            warehouse = self.warehouse
            if not warehouse and self.purchase:
                warehouse = self.purchase.warehouse
            if warehouse and getattr(warehouse, 'storage_location', None):
                stock_context = {
                    'locations': [warehouse.storage_location.id],
                    'with_childs': True,
                }

        if stock_context:
            with Transaction().set_context(**stock_context):
                values = Product.get_quantity([self.product], quantity_name)
        else:
            values = Product.get_quantity([self.product], quantity_name)
        return values.get(self.product.id, 0.0)

