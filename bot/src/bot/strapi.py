from urllib.parse import urljoin

import requests


def get_products(strapi_url, strapi_token):
    response = requests.get(
        f"{strapi_url}/api/products",
        headers={"Authorization": f"Bearer {strapi_token}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def get_product(strapi_url, strapi_token, document_id):
    response = requests.get(
        f"{strapi_url}/api/products/{document_id}",
        headers={"Authorization": f"Bearer {strapi_token}"},
        params={"populate": "picture"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def get_picture(strapi_url, picture_url):
    response = requests.get(urljoin(strapi_url, picture_url), timeout=10)
    response.raise_for_status()
    return response.content