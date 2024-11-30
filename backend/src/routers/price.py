from fastapi import APIRouter, Query
import requests

router = APIRouter()

@router.get("/api/v1/prices/necessities-price")
async def get_necessities_prices(
    category: str = Query(None), 
    commodity: str = Query(None)
):
    """取得民生物價資料"""
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json() 
    """
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch necessities prices")
    return response.json()
    """