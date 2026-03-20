from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    quantity = fields.Function(
        fields.Float('Stock', digits='default_uom', readonly=True),
        'get_quantity', searcher='search_quantity')
    forecast_quantity = fields.Function(
        fields.Float('Stock Previsto', digits='default_uom', readonly=True),
        'get_quantity', searcher='search_quantity')

    @classmethod
    def _get_default_stock_context(cls):
        context = Transaction().context
        if context.get('locations'):
            return {}

        Location = Pool().get('stock.location')

        warehouse_id = context.get('warehouse')
        if warehouse_id:
            warehouse = Location(warehouse_id)
            storage_location = getattr(warehouse, 'storage_location', None)
            if storage_location:
                return {
                    'locations': [storage_location.id],
                    'with_childs': True,
                }

        domain = [('type', '=', 'warehouse')]
        company = context.get('company')
        if company and 'company' in Location._fields:
            domain.append(('company', '=', company))

        warehouses = Location.search(domain)
        locations = [
            warehouse.storage_location.id
            for warehouse in warehouses
            if getattr(warehouse, 'storage_location', None)
        ]
        if not locations:
            return {}
        return {
            'locations': locations,
            'with_childs': True,
        }

    @classmethod
    def get_quantity(cls, products, name):
        stock_context = cls._get_default_stock_context()
        if not stock_context:
            return super().get_quantity(products, name)

        with Transaction().set_context(**stock_context):
            return super().get_quantity(products, name)

    @classmethod
    def search_quantity(cls, name, domain=None):
        stock_context = cls._get_default_stock_context()
        if not stock_context:
            return super().search_quantity(name, domain)

        with Transaction().set_context(**stock_context):
            return super().search_quantity(name, domain)

    def get_rec_name(self, name):
        rec_name = super().get_rec_name(name)
        code = getattr(self, 'code', None) or getattr(self, 'suffix_code', None)
        if code:
            return f'[{code}] {rec_name}'
        return rec_name


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    quantity = fields.Function(
        fields.Float('Stock', digits='default_uom', readonly=True),
        'sum_extended_product')
    forecast_quantity = fields.Function(
        fields.Float('Stock Previsto', digits='default_uom', readonly=True),
        'sum_extended_product')

    def sum_extended_product(self, name):
        return super().sum_product(name)
