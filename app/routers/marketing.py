from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import Organization, SubscriptionPlan
from app.schemas import AppConfigOut, OrganizationOut, PlanOut

router = APIRouter(tags=['marketing'])


@router.get('/membership-plans', response_model=list[PlanOut])
def list_membership_plans(db: Session = Depends(get_db)):
    return db.query(SubscriptionPlan).order_by(SubscriptionPlan.id.asc()).all()


@router.get('/organizations', response_model=list[OrganizationOut])
def list_organizations(db: Session = Depends(get_db)):
    return db.query(Organization).options(joinedload(Organization.plan)).order_by(Organization.organization_name.asc()).all()


@router.get('/app-config', response_model=AppConfigOut)
def get_app_config(db: Session = Depends(get_db)):
    plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.id.asc()).all()
    return AppConfigOut(
        product_name='Magnetly',
        vertical='D2C Home Goods',
        ideal_customer='Fast growing D2C home goods brands that have outgrown spreadsheets and disconnected dashboards.',
        memberships=[PlanOut.model_validate(plan) for plan in plans],
    )
