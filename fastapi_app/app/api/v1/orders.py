# fastapi_app/app/api/v1/orders.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.orders import OrderCreate, OrderResponse
from app.services.ls_securities import LSSecuritiesClient

router = APIRouter()
ls_client = LSSecuritiesClient()


@router.post("/place", response_model=OrderResponse)
async def place_order(order: OrderCreate):
    try:
        result = await ls_client.place_order(order)
        print(result["rsp_msg"])
        # 응답 처리 : TODO: response 데이터 확인할것 'error'필드가 있는지지
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return OrderResponse(
            order_id=result.get("OrdNo", ""),
            status="success",
            message="주문 요청했습니다.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(f"예외닷! {e}"))
