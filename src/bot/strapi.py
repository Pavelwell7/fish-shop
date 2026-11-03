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


def get_or_create_cart(strapi_url, strapi_token, tg_id):
    headers = {"Authorization": f"Bearer {strapi_token}"}

    response = requests.get(
        f"{strapi_url}/api/carts",
        headers=headers,
        params={"filters[tg_id][$eq]": tg_id},
        timeout=10,
    )
    response.raise_for_status()
    carts = response.json()["data"]
    if carts:
        return carts[0]

    response = requests.post(
        f"{strapi_url}/api/carts",
        headers=headers,
        json={"data": {"tg_id": str(tg_id)}},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def add_product_to_cart(
    strapi_url,
    strapi_token,
    cart_document_id,
    product_document_id,
    quantity=1,
):
    headers = {"Authorization": f"Bearer {strapi_token}"}

    response = requests.post(
        f"{strapi_url}/api/cart-items",
        headers=headers,
        json={
            "data": {
                "quantity": quantity,
                "product": {"connect": [product_document_id]},
            }
        },
        timeout=10,
    )
    response.raise_for_status()
    cart_item = response.json()["data"]

    response = requests.put(
        f"{strapi_url}/api/carts/{cart_document_id}",
        headers=headers,
        json={"data": {"cart_items": {"connect": [cart_item["documentId"]]}}},
        timeout=10,
    )
    response.raise_for_status()


def get_cart(strapi_url, strapi_token, tg_id):
    response = requests.get(
        f"{strapi_url}/api/carts",
        headers={"Authorization": f"Bearer {strapi_token}"},
        params={
            "filters[tg_id][$eq]": tg_id,
            "populate[cart_items][populate]": "product",
        },
        timeout=10,
    )
    response.raise_for_status()
    carts = response.json()["data"]
    return carts[0] if carts else None


def delete_cart_item(strapi_url, strapi_token, cart_item_document_id):
    response = requests.delete(
        f"{strapi_url}/api/cart-items/{cart_item_document_id}",
        headers={"Authorization": f"Bearer {strapi_token}"},
        timeout=10,
    )
    if response.status_code != 404:
        response.raise_for_status()


def save_client(strapi_url, strapi_token, tg_id, email):
    headers = {"Authorization": f"Bearer {strapi_token}"}

    client = get_client(strapi_url, strapi_token, tg_id)
    if client:
        response = requests.put(
            f"{strapi_url}/api/clients/{client['documentId']}",
            headers=headers,
            json={"data": {"email": email}},
            timeout=10,
        )
    else:
        response = requests.post(
            f"{strapi_url}/api/clients",
            headers=headers,
            json={"data": {"tg_id": str(tg_id), "email": email}},
            timeout=10,
        )
    response.raise_for_status()
    return response.json()["data"]


def get_client(strapi_url, strapi_token, tg_id):
    response = requests.get(
        f"{strapi_url}/api/clients",
        headers={"Authorization": f"Bearer {strapi_token}"},
        params={"filters[tg_id][$eq]": tg_id},
        timeout=10,
    )
    response.raise_for_status()
    clients = response.json()["data"]
    return clients[0] if clients else None
