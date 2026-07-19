"""Compatibility facade for the historical profile terminology.

New code should import product definitions from :mod:`jobfinder.products`.
"""

from __future__ import annotations

from jobfinder.products import (
    DEFAULT_PRODUCT,
    LEGACY_PRODUCT_ENV,
    PHDFINDER_PRODUCT_DIR,
    PRODUCT_ALIASES,
    PRODUCTS,
    FinderProduct,
    FinderProductError,
    product_cv_drive_folder_id,
    product_from_env,
    product_spreadsheet_id,
    resolve_product,
)

DEFAULT_PROFILE = DEFAULT_PRODUCT
PROFILE_ENV = LEGACY_PRODUCT_ENV
PROFILE_ALIASES = PRODUCT_ALIASES
PROFILES = PRODUCTS
PHD_PROFILE_DIR = PHDFINDER_PRODUCT_DIR
FinderProfile = FinderProduct
FinderProfileError = FinderProductError
resolve_profile = resolve_product
profile_from_env = product_from_env
profile_spreadsheet_id = product_spreadsheet_id
profile_cv_drive_folder_id = product_cv_drive_folder_id

__all__ = [
    "DEFAULT_PROFILE",
    "FinderProfile",
    "FinderProfileError",
    "PHD_PROFILE_DIR",
    "PROFILE_ALIASES",
    "PROFILE_ENV",
    "PROFILES",
    "profile_cv_drive_folder_id",
    "profile_from_env",
    "profile_spreadsheet_id",
    "resolve_profile",
]
