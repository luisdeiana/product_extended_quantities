from trytond.pool import Pool

from . import product, sale, purchase


def register():
    Pool.register(
        product.Product,
        product.Template,
        sale.SaleLine,
        purchase.PurchaseLine,
        module='product_extended_quantities', type_='model')
