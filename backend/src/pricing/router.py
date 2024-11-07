from fastapi import APIRouter, Query
import requests

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    """
    這個 API 端點從政府開放數據平台檢索生活必需品的價格資訊。

    :param category: 商品類別名稱，可選參數，用於篩選特定商品類別。
    :param commodity: 商品名稱，可選參數，用於篩選特定商品。
    :return: JSON 格式的商品價格資訊，包括商品類別、名稱、價格和地點等細節。
    """
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()