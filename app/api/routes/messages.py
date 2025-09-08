from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional

from ...domain.schemas import MessageIn, SuccessResponse, ErrorResponse, MessageOut, ErrorDetail
from ...services.message_service import InvalidSenderError
from ...repositories.message_repository import DuplicateMessageIdError
from ..deps import get_message_service, get_api_key, rate_limit

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=SuccessResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
})
def create_message(
    payload: MessageIn,
    _: str | None = Depends(get_api_key),
    __: None = Depends(rate_limit),
    service = Depends(get_message_service),
):
    try:
        out: MessageOut = service.process_and_store(payload)
        return {"status": "success", "data": out}
    except InvalidSenderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={
            "code": "INVALID_FORMAT",
            "message": "Formato de mensaje inválido",
            "details": str(e),
        })
    except DuplicateMessageIdError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "code": "DUPLICATE_MESSAGE_ID",
            "message": "message_id ya existe",
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "code": "SERVER_ERROR",
            "message": "Error del servidor",
        })


@router.get("/{session_id}", response_model=dict, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
})
def list_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sender: Optional[str] = Query(default=None, pattern="^(user|system)$"),
    _: str | None = Depends(get_api_key),
    __: None = Depends(rate_limit),
    service = Depends(get_message_service),
):
    items = service.list_by_session(session_id=session_id, limit=limit, offset=offset, sender=sender)
    return {"status": "success", "data": [i.model_dump() for i in items]}
