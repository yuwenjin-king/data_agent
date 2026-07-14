import io
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.knowledge import AgentKnowledge, AgentPresetQuestion, SemanticModel
from app.schemas.knowledge import (
    AgentKnowledgeCreate,
    AgentKnowledgeQueryRequest,
    AgentKnowledgeUpdate,
    AgentPresetQuestionCreate,
    BatchImportResult,
    SemanticModelBatchImportItem,
    SemanticModelCreate,
    SemanticModelUpdate,
)
from app.services.crud_base import CRUDBase
from app.services.datasource_service import agent_datasource_crud
from app.utils.chunking import chunk_text
from app.utils.file_storage import delete_file, read_file_text, save_upload_file


class CRUDSemanticModel(CRUDBase[SemanticModel, SemanticModelCreate, SemanticModelUpdate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[SemanticModel]:
        return db.query(SemanticModel).filter(
            and_(
                SemanticModel.agent_id == agent_id,
                SemanticModel.status == 1
            )
        ).offset(skip).limit(limit).all()

    def get_by_table(
        self, db: Session, *, agent_id: int, datasource_id: int, table_name: str
    ) -> List[SemanticModel]:
        return db.query(SemanticModel).filter(
            and_(
                SemanticModel.agent_id == agent_id,
                SemanticModel.datasource_id == datasource_id,
                SemanticModel.table_name == table_name,
                SemanticModel.status == 1
            )
        ).all()

    def search(
        self, db: Session, *, agent_id: Optional[int] = None, keyword: Optional[str] = None,
        status: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[SemanticModel]:
        query = db.query(SemanticModel)
        if agent_id is not None:
            query = query.filter(SemanticModel.agent_id == agent_id)
        if status is not None:
            query = query.filter(SemanticModel.status == status)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (SemanticModel.table_name.like(like))
                | (SemanticModel.column_name.like(like))
                | (SemanticModel.business_name.like(like))
                | (SemanticModel.business_description.like(like))
                | (SemanticModel.synonyms.like(like))
            )
        return query.offset(skip).limit(limit).all()

    def _resolve_active_datasource_id(self, db: Session, agent_id: int) -> int:
        link = agent_datasource_crud.get_active_by_agent(db, agent_id=agent_id)
        if link:
            return link.datasource_id
        link = db.query(agent_datasource_crud.model).filter(
            agent_datasource_crud.model.agent_id == agent_id
        ).order_by(agent_datasource_crud.model.create_time.desc()).first()
        if link:
            return link.datasource_id
        raise ValueError(f"No datasource found for agent {agent_id}")

    def create(self, db: Session, obj_in: SemanticModelCreate) -> SemanticModel:
        obj_data = self._dump_schema(obj_in)
        agent = db.query(Agent).filter(Agent.id == obj_data["agent_id"]).first()
        if not agent:
            raise ValueError(f"Agent {obj_data['agent_id']} not found")
        if not obj_data.get("datasource_id"):
            obj_data["datasource_id"] = self._resolve_active_datasource_id(db, obj_data["agent_id"])
        obj_data["status"] = 1
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_agent_table_column(
        self, db: Session, *, agent_id: int, table_name: str, column_name: str
    ) -> Optional[SemanticModel]:
        return db.query(SemanticModel).filter(
            and_(
                SemanticModel.agent_id == agent_id,
                SemanticModel.table_name == table_name,
                SemanticModel.column_name == column_name,
            )
        ).first()

    def batch_import(
        self, db: Session, *, agent_id: int, items: List[SemanticModelBatchImportItem]
    ) -> BatchImportResult:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        datasource_id = self._resolve_active_datasource_id(db, agent_id)

        errors = []
        success_count = 0
        for item in items:
            try:
                existing = self.get_by_agent_table_column(
                    db, agent_id=agent_id, table_name=item.table_name, column_name=item.column_name
                )
                if existing:
                    existing.business_name = item.business_name
                    existing.synonyms = item.synonyms
                    existing.business_description = item.business_description
                    existing.column_comment = item.column_comment
                    existing.data_type = item.data_type
                    existing.status = 1
                    db.add(existing)
                else:
                    db_obj = SemanticModel(
                        agent_id=agent_id,
                        datasource_id=datasource_id,
                        table_name=item.table_name,
                        column_name=item.column_name,
                        business_name=item.business_name,
                        synonyms=item.synonyms,
                        business_description=item.business_description,
                        column_comment=item.column_comment,
                        data_type=item.data_type,
                        status=1,
                    )
                    db.add(db_obj)
                success_count += 1
            except Exception as exc:
                errors.append(f"{item.table_name}.{item.column_name}: {exc}")
        db.commit()
        return BatchImportResult(
            total=len(items),
            success_count=success_count,
            fail_count=len(errors),
            errors=errors,
        )

    def batch_delete(self, db: Session, *, ids: List[int]) -> int:
        count = db.query(SemanticModel).filter(SemanticModel.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return count

    def enable(self, db: Session, *, id: int) -> Optional[SemanticModel]:
        obj = self.get(db, id=id)
        if not obj:
            return None
        obj.status = 1
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def disable(self, db: Session, *, id: int) -> Optional[SemanticModel]:
        obj = self.get(db, id=id)
        if not obj:
            return None
        obj.status = 0
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def import_excel(
        self, db: Session, *, agent_id: int, upload_file: UploadFile
    ) -> BatchImportResult:
        import pandas as pd
        content = upload_file.file.read()
        df = pd.read_excel(io.BytesIO(content))
        df.columns = [str(c).strip().lower().replace("*", "") for c in df.columns]
        column_map = {
            "表名": "table_name", "tablename": "table_name",
            "字段名": "column_name", "columnname": "column_name",
            "业务名称": "business_name", "businessname": "business_name",
            "数据类型": "data_type", "datatype": "data_type",
            "同义词": "synonyms",
            "业务描述": "business_description", "businessdesc": "business_description",
            "description": "business_description", "desc": "business_description",
            "字段注释": "column_comment", "columncomment": "column_comment",
            "创建时间": "create_time",
        }
        df = df.rename(columns=column_map)

        required = ["table_name", "column_name", "business_name", "data_type"]
        errors = []
        items = []
        for idx, row in df.iterrows():
            row_dict = row.where(pd.notnull(row), None).to_dict()
            missing = [c for c in required if not row_dict.get(c)]
            if missing:
                errors.append(f"Row {idx + 2}: missing {missing}")
                continue
            items.append(SemanticModelBatchImportItem(
                table_name=str(row_dict["table_name"]).strip(),
                column_name=str(row_dict["column_name"]).strip(),
                business_name=str(row_dict["business_name"]).strip(),
                data_type=str(row_dict["data_type"]).strip(),
                synonyms=_to_str_or_none(row_dict.get("synonyms")),
                business_description=_to_str_or_none(row_dict.get("business_description")),
                column_comment=_to_str_or_none(row_dict.get("column_comment")),
            ))
        if not items:
            return BatchImportResult(total=len(df), success_count=0, fail_count=len(errors), errors=errors)
        result = self.batch_import(db, agent_id=agent_id, items=items)
        result.errors.extend(errors)
        result.fail_count += len(errors)
        return result

    def generate_template_bytes(self) -> bytes:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "semantic_model_template"
        headers = ["表名*", "字段名*", "业务名称*", "数据类型*", "同义词", "业务描述", "字段注释", "创建时间"]
        ws.append(headers)
        ws.append(["orders", "amount", "订单金额", "decimal", "销售额,GMV", "订单金额", "", ""])
        ws.append(["users", "id", "用户ID", "bigint", "", "用户唯一标识", "", ""])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.read()


class CRUDAgentKnowledge(CRUDBase[AgentKnowledge, AgentKnowledgeCreate, AgentKnowledgeUpdate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentKnowledge]:
        return db.query(AgentKnowledge).filter(
            and_(
                AgentKnowledge.agent_id == agent_id,
                AgentKnowledge.is_deleted == 0
            )
        ).offset(skip).limit(limit).all()

    @staticmethod
    def _apply_defaults(obj_data: dict) -> dict:
        obj_data.setdefault("is_recall", 1)
        obj_data.setdefault("is_deleted", 0)
        obj_data.setdefault("embedding_status", "PENDING")
        obj_data.setdefault("is_resource_cleaned", 0)
        obj_data.setdefault("splitter_type", "token")
        return obj_data

    def create(self, db: Session, obj_in: AgentKnowledgeCreate) -> AgentKnowledge:
        obj_data = self._dump_schema(obj_in)
        obj_data = self._apply_defaults(obj_data)
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_with_file(
        self, db: Session, *,
        agent_id: int, title: str, type: str,
        question: Optional[str], content: Optional[str],
        is_recall: int, splitter_type: str,
        upload_file: Optional[UploadFile]
    ) -> AgentKnowledge:
        if type == "DOCUMENT":
            if not upload_file or not upload_file.filename:
                raise ValueError("DOCUMENT knowledge requires a file upload")
        elif type in ("QA", "FAQ"):
            if not question or not content:
                raise ValueError(f"{type} knowledge requires both question and content")
        else:
            raise ValueError(f"Unsupported knowledge type: {type}")

        file_meta = {}
        if upload_file:
            file_meta = save_upload_file(upload_file, "agent-knowledge")

        obj_data = {
            "agent_id": agent_id,
            "title": title,
            "type": type,
            "question": question,
            "content": content,
            "is_recall": is_recall,
            "splitter_type": splitter_type,
            **file_meta,
        }
        obj_data = self._apply_defaults(obj_data)
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_fields(
        self, db: Session, *, id: int, obj_in: AgentKnowledgeUpdate
    ) -> Optional[AgentKnowledge]:
        obj = self.get(db, id=id)
        if not obj:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def set_recall(self, db: Session, *, id: int, is_recall: int) -> Optional[AgentKnowledge]:
        obj = self.get(db, id=id)
        if not obj:
            return None
        obj.is_recall = is_recall
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_soft(self, db: Session, *, id: int) -> Optional[AgentKnowledge]:
        obj = self.get(db, id=id)
        if not obj:
            return None
        obj.is_deleted = 1
        if obj.file_path:
            delete_file(obj.file_path)
            obj.is_resource_cleaned = 1
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def query_page(self, db: Session, *, request: AgentKnowledgeQueryRequest) -> dict:
        query = db.query(AgentKnowledge).filter(AgentKnowledge.is_deleted == 0)
        if request.agent_id is not None:
            query = query.filter(AgentKnowledge.agent_id == request.agent_id)
        if request.type:
            query = query.filter(AgentKnowledge.type == request.type)
        if request.embedding_status:
            query = query.filter(AgentKnowledge.embedding_status == request.embedding_status)
        if request.is_recall is not None:
            query = query.filter(AgentKnowledge.is_recall == request.is_recall)
        if request.keyword:
            like = f"%{request.keyword}%"
            query = query.filter(
                (AgentKnowledge.title.like(like))
                | (AgentKnowledge.question.like(like))
                | (AgentKnowledge.content.like(like))
            )

        total = query.with_entities(func.count(AgentKnowledge.id)).scalar()
        page = max(request.page, 1)
        page_size = max(min(request.page_size, 100), 1)
        skip = (page - 1) * page_size
        items = query.offset(skip).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def retry_embedding(self, db: Session, *, id: int) -> Optional[AgentKnowledge]:
        obj = self.get(db, id=id)
        if not obj:
            return None
        if obj.embedding_status == "PROCESSING":
            raise ValueError("Embedding is already in progress")
        if obj.is_recall == 0:
            raise ValueError("Cannot retry embedding when is_recall is disabled")
        obj.embedding_status = "PENDING"
        obj.error_msg = None
        db.add(obj)
        db.commit()
        db.refresh(obj)
        _run_embedding_stub(db, obj)
        return obj


class CRUDAgentPresetQuestion(CRUDBase[AgentPresetQuestion, AgentPresetQuestionCreate, AgentPresetQuestionCreate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentPresetQuestion]:
        return db.query(AgentPresetQuestion).filter(
            and_(
                AgentPresetQuestion.agent_id == agent_id,
                AgentPresetQuestion.is_active == 1
            )
        ).order_by(AgentPresetQuestion.sort_order).offset(skip).limit(limit).all()


def _to_str_or_none(value) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def _run_embedding_stub(db: Session, knowledge: AgentKnowledge) -> None:
    """Synchronous embedding stub: transitions status without real vector store."""
    knowledge.embedding_status = "PROCESSING"
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)

    try:
        if knowledge.type == "DOCUMENT" and knowledge.file_path:
            text = read_file_text(knowledge.file_path)
        elif knowledge.type in ("QA", "FAQ"):
            text = knowledge.question or ""
        else:
            text = knowledge.content or ""
        chunk_text(text, splitter_type=knowledge.splitter_type or "token")
        knowledge.embedding_status = "COMPLETED"
        knowledge.error_msg = None
    except Exception as exc:
        knowledge.embedding_status = "FAILED"
        knowledge.error_msg = str(exc)[:255]

    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)


semantic_model_crud = CRUDSemanticModel(SemanticModel)
agent_knowledge_crud = CRUDAgentKnowledge(AgentKnowledge)
agent_preset_question_crud = CRUDAgentPresetQuestion(AgentPresetQuestion)
