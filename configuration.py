from trytond.model import fields
from trytond.pool import Pool, PoolMeta


def default_func(field_name):
    @classmethod
    def default(cls, **pattern):
        return getattr(
            cls.multivalue_model(field_name),
            'default_%s' % field_name, lambda: None)()
    return default


class Configuration(metaclass=PoolMeta):
    __name__ = 'sale.configuration'

    peq_filter_products_by_stock = fields.MultiValue(fields.Boolean(
        'Filtrar productos por stock'))
    peq_filter_products_by_forecast = fields.MultiValue(fields.Boolean(
        'Usar stock previsto para filtrar'))
    peq_unordered_product_search = fields.MultiValue(fields.Boolean(
        'Busqueda de productos sin orden de palabras'))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {
                'peq_filter_products_by_stock',
                'peq_filter_products_by_forecast',
                'peq_unordered_product_search'}:
            return pool.get('sale.configuration.sale_method')
        return super().multivalue_model(field)

    default_peq_filter_products_by_stock = default_func(
        'peq_filter_products_by_stock')
    default_peq_filter_products_by_forecast = default_func(
        'peq_filter_products_by_forecast')
    default_peq_unordered_product_search = default_func(
        'peq_unordered_product_search')


class ConfigurationSaleMethod(metaclass=PoolMeta):
    __name__ = 'sale.configuration.sale_method'

    peq_filter_products_by_stock = fields.Boolean('Filtrar productos por stock')
    peq_filter_products_by_forecast = fields.Boolean(
        'Usar stock previsto para filtrar')
    peq_unordered_product_search = fields.Boolean(
        'Busqueda de productos sin orden de palabras')

    @classmethod
    def default_peq_filter_products_by_stock(cls):
        return True

    @classmethod
    def default_peq_filter_products_by_forecast(cls):
        return True

    @classmethod
    def default_peq_unordered_product_search(cls):
        return False
