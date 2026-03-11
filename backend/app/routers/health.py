from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health", summary="健康检查", description="检查服务是否正常运行，返回状态与消息。")
def health() -> dict:
    return {"status": "正常", "message": "服务运行正常"}

