from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import KeywordTrend
from app.schemas import TrendOut

router = APIRouter(tags=['trends'])


@router.get('/trends', response_model=list[TrendOut])
def get_trends(db: Session = Depends(get_db)):
    return db.query(KeywordTrend).order_by(KeywordTrend.trend_week.desc(), KeywordTrend.mention_count.desc()).limit(50).all()
