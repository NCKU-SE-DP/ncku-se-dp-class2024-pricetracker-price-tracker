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
    Get the prices of necessities.

    :param category: The category of the commodity.
    :type category: str, optional
    :param commodity: The name of the commodity.
    :type commodity: str, optional
    :return: JSON response containing the prices of necessities.
    :rtype: dict
    """
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()
