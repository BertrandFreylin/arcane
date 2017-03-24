#-*- coding: utf-8 -*-
from django.http import HttpResponse
from requests import HTTPError
from requests import Session
from arcane.settings import API_KEY_PRESTA, PRESTA_HOST
import xmltodict
from django.views.generic import TemplateView
import csv


def get_info_presta(info):

    content = Session().get(PRESTA_HOST+'/'+'/'.join(info)+'/'+'?ws_key='+API_KEY_PRESTA).content
    if not content:
        raise HTTPError('Content response is empty')
    else:
        parsed_content = xmltodict.parse(content)
    return parsed_content


def get_price():
    parsed_content = get_info_presta(['products'])
    product_listing = []
    for product in parsed_content['prestashop']['products']['product']:
        product_id = product['@id']
        product_detail = get_info_presta(['products', product_id])
        if int(product_detail['prestashop']['product']['active']):
            name = product_detail['prestashop']['product']['name']['language']['#text']
            price = float(product_detail['prestashop']['product']['price'])
            formated_name = product_detail['prestashop']['product']['link_rewrite']['language']['#text']

            presta_url = 'http://104.155.108.210/home/' + product_id + '-' + formated_name + '.html'
            fnac_url = 'http://recherche.fnac.com/SearchResult/ResultList.aspx?Search=' + formated_name.split('-')[-1]
            amazon_url = 'https://www.amazon.fr/s/ref=nb_sb_noss?field-keywords=' + formated_name.split('-')[-1]
            darty_url = 'http://www.darty.com/nav/recherche?text=' + formated_name.split('-')[-1]

            fnac_price = None
            amazon_price = None
            darty_price = None

            fnac_product = Session().get(fnac_url).content.replace('\r', '').replace('\n', '').replace(' ', '').split(
                '<pclass="Article-desc">')
            if fnac_product:
                product_fnac_name = fnac_product[1].split('<ahref="http://www.fnac.com/')
                if product_fnac_name and len(product_fnac_name) > 1 and formated_name.split('-')[-1].upper() in \
                        product_fnac_name[1].split('class="js-minifa-title"')[0]:
                    fnac_price = float(fnac_product[1].split('userPrice">')[1].split('<sup>')[0] + '.' +
                                       fnac_product[1].split('userPrice">')[1].split('</sup>')[0].split('&euro;')[1])

            amazon_product = Session().get(amazon_url).content
            if amazon_product and 'migrating to our APIs' in amazon_product:
                amazon_price = 'API blocked'
            elif amazon_product:
                product_amazon_name = amazon_product[1].split('<ahref="http://www.amazon.com/')
                if product_amazon_name and len(product_amazon_name) > 1 and formated_name.split('-')[-1].upper() in \
                        product_amazon_name[1].split('class="js-minifa-title"')[0]:
                    amazon_price = float(amazon_product[1].split('userPrice">')[1].split('<sup>')[0] + '.' +
                                         amazon_product[1].split('userPrice">')[1].split('</sup>')[0].split(
                                             '&euro;')[1])

            darty_product = Session().get(darty_url).content.replace('\r', '').replace('\n', '').replace(' ', '').split(
                '<pclass="Article-desc">')
            if darty_product and len(darty_product) > 1:
                product_darty_name = darty_product[1].split('<ahref="http://www.darty.com/')
                if product_darty_name and len(product_darty_name) > 1 and formated_name.split('-')[-1].upper() in \
                        product_darty_name[1].split('class="js-minifa-title"')[0]:
                    darty_price = float(darty_product[1].split('userPrice">')[1].split('<sup>')[0] + '.' +
                                        darty_product[1].split('userPrice">')[1].split('</sup>')[0].split('&euro;')[1])

            product_listing.append({'name': name,
                                    'price': price,
                                    'fnac_price': fnac_price,
                                    'amazon_price': amazon_price,
                                    'darty_price': darty_price,
                                    'presta_url': presta_url,
                                    'fnac_url': fnac_url,
                                    'amazon_url': amazon_url,
                                    'darty_url': darty_url})
    return product_listing


def export_csv(request):
    product_listing = get_price()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export-product.csv"'
    writer = csv.writer(response)
    writer.writerow(['Product', 'Price Presta', 'Price Fnac', 'Price Amazon', 'Price Darty'])
    for product in product_listing:
        fnac_price = product['fnac_price'] if product['fnac_price'] else 'No product found'
        amazon_price = product['amazon_price'] if product['amazon_price'] else 'No product found'
        darty_price = product['darty_price'] if product['darty_price'] else 'No product found'
        writer.writerow([product['name'], product['price'], fnac_price, amazon_price, darty_price])
    return response


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['product_listing'] = get_price()
        return context

