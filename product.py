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
    code_display = fields.Function(
        fields.Char('Codigo', readonly=True),
        'on_change_with_code_display')

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

    @fields.depends('code', 'suffix_code')
    def on_change_with_code_display(self, name=None):
        return (self.code or self.suffix_code or '')

    @classmethod
    def search_rec_name(cls, name, clause):
        context = Transaction().context

        _, operator, operand, *extra = clause
        if isinstance(operand, str):
            raw_text = operand.strip()
            normalized = raw_text.replace('%', '').strip()
            if operator.endswith('like') and len(normalized) < 3:
                return [('id', '=', None)]

        base_domain = super().search_rec_name(name, clause)

        search_domain = base_domain

        if context.get('peq_unordered_product_search'):
            if (isinstance(operand, str)
                    and operator.endswith('like')
                    and len(operand.split()) > 1):
                words = [w.strip('%') for w in operand.split() if w.strip('%')]
                if words:
                    words_domain = ['AND']
                    for word in words:
                        clean_word = word.strip('[](){}')
                        value = f'%{clean_word}%'
                        words_domain.append(['OR',
                            ('code', operator, value, *extra),
                            ('suffix_code', operator, value, *extra),
                            ('identifiers.code', operator, value, *extra),
                            ('template.name', operator, value, *extra),
                            ('template.code', operator, value, *extra),
                            ])
                    search_domain = words_domain

        if not context.get('peq_filter_products_by_stock'):
            return search_domain

        # Pre-filtered search: find matching products by text first (fast,
        # uses indexes), then compute stock only for those results.  This
        # avoids the expensive full-table stock aggregation that the ORM
        # would trigger when evaluating (quantity > 0) as a domain clause.
        quantity_field = ('forecast_quantity'
            if context.get('peq_filter_products_by_forecast', True)
            else 'quantity')

        products = cls.search(search_domain)
        if not products:
            return [('id', '=', None)]

        stock_context = cls._get_default_stock_context()
        if stock_context:
            with Transaction().set_context(**stock_context):
                quantities = cls.get_quantity(products, quantity_field)
        else:
            quantities = cls.get_quantity(products, quantity_field)

        result_ids = [
            p.id for p in products
            if p.type != 'goods' or quantities.get(p.id, 0) > 0
        ]
        if not result_ids:
            return [('id', '=', None)]
        return [('id', 'in', result_ids)]

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
