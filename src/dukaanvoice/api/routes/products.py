from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dukaanvoice.api.dependencies import get_product_repository
from dukaanvoice.repositories.json_product_repository import JSONProductRepository
from dukaanvoice.schemas.product import ProductSchema

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductSchema])
def list_products(
    repository: JSONProductRepository = Depends(get_product_repository),
) -> list[ProductSchema]:
    return [
        ProductSchema(
            product_id=product.product_id,
            canonical_name=product.canonical_name,
            brand=product.brand,
            category=product.category,
            pack_size=product.pack_size,
            unit=product.unit,
            price=product.price,
            available_stock=product.available_stock,
            alternative_product_ids=product.alternative_product_ids,
            is_active=product.is_active,
        )
        for product in repository.list_products()
    ]


@router.get("/{product_id}", response_model=ProductSchema)
def get_product(
    product_id: str,
    repository: JSONProductRepository = Depends(get_product_repository),
) -> ProductSchema:
    product = repository.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return ProductSchema(
        product_id=product.product_id,
        canonical_name=product.canonical_name,
        brand=product.brand,
        category=product.category,
        pack_size=product.pack_size,
        unit=product.unit,
        price=product.price,
        available_stock=product.available_stock,
        alternative_product_ids=product.alternative_product_ids,
        is_active=product.is_active,
    )
