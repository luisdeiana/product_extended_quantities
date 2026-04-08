from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    filter_products_by_stock = fields.Boolean('Filtrar productos por stock')
    filter_products_by_forecast = fields.Boolean(
        'Usar stock previsto para filtrar')
    unordered_product_search = fields.Boolean(
        'Busqueda de productos sin orden de palabras')

    @staticmethod
    def _get_peq_default(field_name, fallback):
        Configuration = Pool().get('sale.configuration')
        config = Configuration(1)
        company = Transaction().context.get('company')
        value = config.get_multivalue(field_name, company=company)
        if value is None:
            return fallback
        return bool(value)

    @classmethod
    def default_filter_products_by_stock(cls):
        return cls._get_peq_default('peq_filter_products_by_stock', True)

    @classmethod
    def default_filter_products_by_forecast(cls):
        return cls._get_peq_default('peq_filter_products_by_forecast', True)

    @classmethod
    def default_unordered_product_search(cls):
        return cls._get_peq_default('peq_unordered_product_search', False)

    @fields.depends('lines', 'filter_products_by_stock', 'filter_products_by_forecast',
        'unordered_product_search')
    def on_change_filter_products_by_stock(self):
        for line in (self.lines or []):
            line.filter_products_by_stock = self.filter_products_by_stock
            line.filter_products_by_forecast = self.filter_products_by_forecast
            line.unordered_product_search = self.unordered_product_search

    @fields.depends('lines', 'filter_products_by_stock', 'filter_products_by_forecast',
        'unordered_product_search')
    def on_change_filter_products_by_forecast(self):
        for line in (self.lines or []):
            line.filter_products_by_stock = self.filter_products_by_stock
            line.filter_products_by_forecast = self.filter_products_by_forecast
            line.unordered_product_search = self.unordered_product_search


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    quantity_available = fields.Function(
        fields.Float('Stock', digits='unit', readonly=True),
        'on_change_with_quantity_available')
    forecast_quantity_available = fields.Function(
        fields.Float('Stock Previsto', digits='unit', readonly=True),
        'on_change_with_forecast_quantity_available')
    filter_products_by_stock = fields.Function(
        fields.Boolean('Filtrar productos por stock'),
        'on_change_with_filter_products_by_stock')
    filter_products_by_forecast = fields.Function(
        fields.Boolean('Usar stock previsto para filtrar'),
        'on_change_with_filter_products_by_forecast')
    unordered_product_search = fields.Function(
        fields.Boolean('Busqueda de productos sin orden de palabras'),
        'on_change_with_unordered_product_search')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        search_context = dict(cls.product.search_context or {})
        search_context.update({
            'peq_filter_products_by_stock': Eval('filter_products_by_stock', False),
            'peq_filter_products_by_forecast': Eval('filter_products_by_forecast', True),
            'peq_unordered_product_search': Eval('unordered_product_search', False),
            })
        cls.product.search_context = search_context
        cls.product.depends.update({
            'filter_products_by_stock',
            'filter_products_by_forecast',
            'unordered_product_search',
            })

    @fields.depends(
        'sale',
        '_parent_sale.filter_products_by_stock',
        '_parent_sale.filter_products_by_forecast',
        '_parent_sale.unordered_product_search')
    def on_change_with_filter_products_by_stock(self, name=None):
        if self.sale:
            return bool(self.sale.filter_products_by_stock)
        return False

    @fields.depends(
        'sale',
        '_parent_sale.filter_products_by_stock',
        '_parent_sale.filter_products_by_forecast',
        '_parent_sale.unordered_product_search')
    def on_change_with_filter_products_by_forecast(self, name=None):
        if self.sale:
            return bool(self.sale.filter_products_by_forecast)
        return True

    @fields.depends(
        'sale',
        '_parent_sale.filter_products_by_stock',
        '_parent_sale.filter_products_by_forecast',
        '_parent_sale.unordered_product_search')
    def on_change_with_unordered_product_search(self, name=None):
        if self.sale:
            return bool(self.sale.unordered_product_search)
        return False

    @fields.depends('product', 'type', 'warehouse', 'sale', '_parent_sale.warehouse')
    def on_change_with_quantity_available(self, name=None):
        return self._on_change_stock_value('quantity')

    @fields.depends('product', 'type', 'warehouse', 'sale', '_parent_sale.warehouse')
    def on_change_with_forecast_quantity_available(self, name=None):
        return self._on_change_stock_value('forecast_quantity')

    @fields.depends('product', 'type', 'warehouse', 'sale', '_parent_sale.warehouse')
    def _on_change_stock_value(self, quantity_name):
        if self.type != 'line' or not self.product:
            return 0.0

        Product = Pool().get('product.product')

        stock_context = Product._get_default_stock_context()
        if not stock_context:
            warehouse = self.warehouse
            if not warehouse and self.sale:
                warehouse = self.sale.warehouse
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
