from fastapi import APIRouter, Query
import requests
router = APIRouter(
    prefix='/prices',
    tags=["Prices", "v1"]
)

@router.get(path='/necessities-price')
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()