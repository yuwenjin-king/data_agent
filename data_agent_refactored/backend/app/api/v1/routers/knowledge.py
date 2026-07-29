import asyncio
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.core.database import get_db
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.knowledge import (
    AgentKnowledgeCreate,
    AgentKnowledgeQueryRequest,
    AgentKnowledgeRecallUpdate,
    AgentKnowledgeResponse,
    AgentKnowledgeUpdate,
    AgentPresetQuestionCreate,
    AgentPresetQuestionResponse,
    BatchImportResult,
    SemanticModelBatchIdsRequest,
    SemanticModelBatchImportRequest,
    SemanticModelCreate,
    SemanticModelResponse,
    SemanticModelUpdate,
)
from app.services.knowledge_service import (
    agent_knowledge_crud,
    agent_preset_question_crud,
    semantic_model_crud,
)
from app.workflow.indexing import (
    delete_agent_knowledge_index,
    index_agent_knowledge,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(require_auth)])


# ---------------------------------------------------------------------------
# SemanticModel endpoints
# ---------------------------------------------------------------------------


@router.get("/semantic-models/template/download")
def download_semantic_model_template():
    data = semantic_model_crud.generate_template_bytes()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=semantic_model_template.xlsx"},
    )


@router.post("/semantic-models/import/excel", response_model=ApiResponse[BatchImportResult])
def import_semantic_models_excel(
    agent_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        result = semantic_model_crud.import_excel(db, agent_id=agent_id, upload_file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiResponse(data=result)


@router.post("/semantic-models/batch-import", response_model=ApiResponse[BatchImportResult])
def batch_import_semantic_models(
    request: SemanticModelBatchImportRequest, db: Session = Depends(get_db)
):
    try:
        result = semantic_model_crud.batch_import(
            db, agent_id=request.agent_id, items=request.items
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiResponse(data=result)


@router.delete("/semantic-models/batch", response_model=ApiResponse)
def batch_delete_semantic_models(
    request: SemanticModelBatchIdsRequest, db: Session = Depends(get_db)
):
    count = semantic_model_crud.batch_delete(db, ids=request.ids)
    return ApiResponse(message=f"Deleted {count} semantic models")


@router.get("/semantic-models", response_model=ApiResponse[List[SemanticModelResponse]])
def list_semantic_models(
    agent_id: Optional[int] = None,
    keyword: Optional[str] = None,
    status: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    models = semantic_model_crud.search(
        db, agent_id=agent_id, keyword=keyword, status=status, skip=skip, limit=limit
    )
    return ApiResponse(data=[SemanticModelResponse.model_validate(m) for m in models])


@router.get(
    "/semantic-models/{semantic_model_id}", response_model=ApiResponse[SemanticModelResponse]
)
def get_semantic_model(semantic_model_id: int, db: Session = Depends(get_db)):
    model = semantic_model_crud.get(db, id=semantic_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Semantic model not found")
    return ApiResponse(data=SemanticModelResponse.model_validate(model))


@router.post("/semantic-models", response_model=ApiResponse[SemanticModelResponse])
def create_semantic_model(model_in: SemanticModelCreate, db: Session = Depends(get_db)):
    try:
        model = semantic_model_crud.create(db, obj_in=model_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiResponse(data=SemanticModelResponse.model_validate(model))


@router.put(
    "/semantic-models/{semantic_model_id}", response_model=ApiResponse[SemanticModelResponse]
)
def update_semantic_model(
    semantic_model_id: int, model_in: SemanticModelUpdate, db: Session = Depends(get_db)
):
    model = semantic_model_crud.get(db, id=semantic_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Semantic model not found")
    model = semantic_model_crud.update(db, db_obj=model, obj_in=model_in)
    return ApiResponse(data=SemanticModelResponse.model_validate(model))


@router.delete("/semantic-models/{semantic_model_id}", response_model=ApiResponse)
def delete_semantic_model(semantic_model_id: int, db: Session = Depends(get_db)):
    model = semantic_model_crud.get(db, id=semantic_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Semantic model not found")
    semantic_model_crud.remove(db, id=semantic_model_id)
    return ApiResponse(message="Semantic model deleted successfully")


@router.put(
    "/semantic-models/{semantic_model_id}/enable", response_model=ApiResponse[SemanticModelResponse]
)
def enable_semantic_model(semantic_model_id: int, db: Session = Depends(get_db)):
    model = semantic_model_crud.enable(db, id=semantic_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Semantic model not found")
    return ApiResponse(data=SemanticModelResponse.model_validate(model))


@router.put(
    "/semantic-models/{semantic_model_id}/disable",
    response_model=ApiResponse[SemanticModelResponse],
)
def disable_semantic_model(semantic_model_id: int, db: Session = Depends(get_db)):
    model = semantic_model_crud.disable(db, id=semantic_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Semantic model not found")
    return ApiResponse(data=SemanticModelResponse.model_validate(model))


# Backward-compatible list by agent
@router.get(
    "/semantic-models/agent/{agent_id}", response_model=ApiResponse[List[SemanticModelResponse]]
)
def list_semantic_models_by_agent(agent_id: int, db: Session = Depends(get_db)):
    models = semantic_model_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[SemanticModelResponse.model_validate(m) for m in models])


# ---------------------------------------------------------------------------
# AgentKnowledge endpoints
# ---------------------------------------------------------------------------


@router.get("/agent-knowledge/{knowledge_id}", response_model=ApiResponse[AgentKnowledgeResponse])
def get_agent_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    knowledge = agent_knowledge_crud.get(db, id=knowledge_id)
    if not knowledge or knowledge.is_deleted == 1:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


@router.post("/agent-knowledge", response_model=ApiResponse[AgentKnowledgeResponse])
def create_agent_knowledge_json(knowledge_in: AgentKnowledgeCreate, db: Session = Depends(get_db)):
    knowledge = agent_knowledge_crud.create(db, obj_in=knowledge_in)
    asyncio.run(index_agent_knowledge(knowledge))
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


@router.post("/agent-knowledge/create", response_model=ApiResponse[AgentKnowledgeResponse])
def create_agent_knowledge_multipart(
    agent_id: int = Form(...),
    title: str = Form(...),
    type: str = Form(...),
    question: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    is_recall: int = Form(1),
    splitter_type: str = Form("token"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    try:
        knowledge = agent_knowledge_crud.create_with_file(
            db,
            agent_id=agent_id,
            title=title,
            type=type,
            question=question,
            content=content,
            is_recall=is_recall,
            splitter_type=splitter_type,
            upload_file=file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    asyncio.run(index_agent_knowledge(knowledge))
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


@router.put("/agent-knowledge/{knowledge_id}", response_model=ApiResponse[AgentKnowledgeResponse])
def update_agent_knowledge(
    knowledge_id: int, knowledge_in: AgentKnowledgeUpdate, db: Session = Depends(get_db)
):
    knowledge = agent_knowledge_crud.update_fields(db, id=knowledge_id, obj_in=knowledge_in)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    asyncio.run(index_agent_knowledge(knowledge))
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


@router.put(
    "/agent-knowledge/{knowledge_id}/recall", response_model=ApiResponse[AgentKnowledgeResponse]
)
def toggle_agent_knowledge_recall(
    knowledge_id: int, request: AgentKnowledgeRecallUpdate, db: Session = Depends(get_db)
):
    knowledge = agent_knowledge_crud.set_recall(db, id=knowledge_id, is_recall=request.is_recall)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    asyncio.run(index_agent_knowledge(knowledge))
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


@router.delete("/agent-knowledge/{knowledge_id}", response_model=ApiResponse)
def delete_agent_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    knowledge = agent_knowledge_crud.delete_soft(db, id=knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    delete_agent_knowledge_index(knowledge_id)
    return ApiResponse(message="Knowledge deleted successfully")


@router.post(
    "/agent-knowledge/query/page", response_model=ApiResponse[PageResponse[AgentKnowledgeResponse]]
)
def query_agent_knowledge_page(request: AgentKnowledgeQueryRequest, db: Session = Depends(get_db)):
    page = agent_knowledge_crud.query_page(db, request=request)
    return ApiResponse(
        data=PageResponse(
            items=[AgentKnowledgeResponse.model_validate(item) for item in page["items"]],
            total=page["total"],
            page=page["page"],
            page_size=page["page_size"],
            total_pages=page["total_pages"],
        )
    )


@router.post(
    "/agent-knowledge/{knowledge_id}/retry-embedding",
    response_model=ApiResponse[AgentKnowledgeResponse],
)
def retry_agent_knowledge_embedding(knowledge_id: int, db: Session = Depends(get_db)):
    try:
        knowledge = agent_knowledge_crud.retry_embedding(db, id=knowledge_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    asyncio.run(index_agent_knowledge(knowledge))
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


# Backward-compatible list by agent
@router.get(
    "/agent-knowledge/agent/{agent_id}", response_model=ApiResponse[List[AgentKnowledgeResponse]]
)
def list_agent_knowledge_by_agent(agent_id: int, db: Session = Depends(get_db)):
    knowledge_list = agent_knowledge_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[AgentKnowledgeResponse.model_validate(k) for k in knowledge_list])


# ---------------------------------------------------------------------------
# Preset question endpoints
# ---------------------------------------------------------------------------


@router.post("/preset-questions", response_model=ApiResponse[AgentPresetQuestionResponse])
def create_preset_question(question_in: AgentPresetQuestionCreate, db: Session = Depends(get_db)):
    question = agent_preset_question_crud.create(db, obj_in=question_in)
    return ApiResponse(data=AgentPresetQuestionResponse.model_validate(question))


@router.get(
    "/preset-questions/agent/{agent_id}",
    response_model=ApiResponse[List[AgentPresetQuestionResponse]],
)
def list_preset_questions(agent_id: int, db: Session = Depends(get_db)):
    questions = agent_preset_question_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[AgentPresetQuestionResponse.model_validate(q) for q in questions])
