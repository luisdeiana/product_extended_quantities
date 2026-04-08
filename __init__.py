from trytond.pool import Pool

from . import configuration, product, sale, purchase


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSaleMethod,
        product.Product,
        product.Template,
        sale.Sale,
        sale.SaleLine,
        purchase.PurchaseLine,
        module='product_extended_quantities', type_='model')
