"""
Payroll Service
Handles payroll processing with AI approval workflow.
"""

import uuid
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Employee, PayrollRecord, RiskAssessment
from app.services.risk_service import RiskService
from app.integrations.squad_api import SquadPaymentProcessor, SquadAPIError
from app.core.config import settings
import json

logger = logging.getLogger(__name__)


class PayrollService:
    """Manages payroll processing and approval workflow."""
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_service = RiskService(db)
        self.squad = SquadPaymentProcessor()
        self.auto_approve_threshold = settings.RISK_SCORE_APPROVAL_THRESHOLD
    
    def process_payroll(
        self,
        employee_ids: List[uuid.UUID],
        amount_per_employee: Optional[Dict[uuid.UUID, float]] = None,
        skip_risk_check: bool = False,
        send_payment: bool = True
    ) -> Dict:
        """
        Process payroll for multiple employees.
        
        Args:
            employee_ids: List of employee UUIDs
            amount_per_employee: Custom amount for each employee (None = use salary)
            skip_risk_check: Admin override for risk checks
            send_payment: Actually send payments (False for dry-run)
            
        Returns:
            Dict with approval status and results
            
        Workflow:
        1. For each employee:
           a. Get or run risk assessment
           b. Decide: auto-approve if score < threshold
           c. Create PayrollRecord
           d. If approved & send_payment: Process via Squad
           e. Update status
        """
        results = {
            "processed": 0,
            "approved": 0,
            "rejected": 0,
            "failed": 0,
            "batch_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "records": []
        }
        
        for employee_id in employee_ids:
            try:
                # Get employee
                employee = self.db.query(Employee).filter(
                    Employee.id == employee_id
                ).first()
                
                if not employee:
                    logger.error(f"Employee {employee_id} not found")
                    results["failed"] += 1
                    continue
                
                # Determine amount
                amount = amount_per_employee.get(employee_id) if amount_per_employee else employee.salary
                
                # Run risk assessment
                if skip_risk_check:
                    risk_score = 0.0
                    approved = True
                    logger.info(f"Payroll {employee.name}: ADMIN OVERRIDE")
                else:
                    risk_assessment = self.risk_service.assess_employee_risk(employee_id)
                    risk_score = risk_assessment.risk_score
                    approved = risk_score < self.auto_approve_threshold
                    logger.info(
                        f"Payroll {employee.name}: risk_score={risk_score:.1f}, "
                        f"approved={approved}"
                    )
                
                # Create payroll record
                payroll = PayrollRecord(
                    id=uuid.uuid4(),
                    employee_id=employee_id,
                    amount=amount,
                    risk_score_at_time=risk_score,
                    approved_by_ai=approved and not skip_risk_check
                )
                
                if approved:
                    payroll.status = PayrollRecord.PaymentStatus.APPROVED
                    results["approved"] += 1
                    
                    # Send payment if requested
                    if send_payment:
                        try:
                            # MVP: Assuming bank details are stored somewhere
                            # In production: query from separate employee_banking table
                            bank_code = "001"  # CBN
                            account = "0000000000"  # Placeholder
                            
                            squad_result = self.squad.create_transfer(
                                recipient_bank_code=bank_code,
                                recipient_account_number=account,
                                amount_in_cents=int(amount * 100),
                                employee_name=employee.name,
                                employee_id=str(employee_id),
                                metadata={"batch_id": results["batch_id"]}
                            )
                            
                            payroll.status = PayrollRecord.PaymentStatus.PROCESSED
                            payroll.squad_transaction_id = squad_result.get("transaction_id")
                            logger.info(f"Payment sent: {employee.name} ({squad_result.get('transaction_id')})")
                        
                        except SquadAPIError as e:
                            payroll.status = PayrollRecord.PaymentStatus.FAILED
                            payroll.notes = str(e)
                            logger.error(f"Payment failed for {employee.name}: {str(e)}")
                            results["failed"] += 1
                
                else:
                    payroll.status = PayrollRecord.PaymentStatus.REJECTED
                    payroll.notes = f"Auto-rejected by AI (risk score: {risk_score:.1f})"
                    results["rejected"] += 1
                
                self.db.add(payroll)
                results["processed"] += 1
                
                # Add to results
                results["records"].append({
                    "payroll_id": str(payroll.id),
                    "employee_name": employee.name,
                    "amount": amount,
                    "status": payroll.status.value,
                    "approved_by_ai": payroll.approved_by_ai,
                    "risk_score": risk_score
                })
            
            except Exception as e:
                logger.error(f"Payroll processing failed for {employee_id}: {str(e)}")
                results["failed"] += 1
        
        self.db.commit()
        logger.info(
            f"Payroll batch complete: {results['processed']} processed, "
            f"approved={results['approved']}, rejected={results['rejected']}"
        )
        
        return results
    
    def get_payroll_records(
        self,
        employee_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[int, List[PayrollRecord]]:
        """Get payroll records with filtering."""
        query = self.db.query(PayrollRecord)
        
        if employee_id:
            query = query.filter(PayrollRecord.employee_id == employee_id)
        
        if status:
            query = query.filter(PayrollRecord.status == status)
        
        total = query.count()
        records = query.order_by(PayrollRecord.processing_date.desc()).offset(skip).limit(limit).all()
        
        return total, records
    
    def reject_payroll(
        self,
        payroll_id: uuid.UUID,
        reason: str
    ) -> bool:
        """Manually reject a payroll record."""
        payroll = self.db.query(PayrollRecord).filter(
            PayrollRecord.id == payroll_id
        ).first()
        
        if not payroll:
            return False
        
        if payroll.status != PayrollRecord.PaymentStatus.PENDING:
            logger.warning(f"Cannot reject payroll {payroll_id}: already {payroll.status.value}")
            return False
        
        payroll.status = PayrollRecord.PaymentStatus.REJECTED
        payroll.notes = reason
        payroll.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Payroll rejected: {payroll_id}, reason={reason}")
        return True
    
    def get_payroll_summary(self, month: str) -> Dict:
        """
        Get summary of payroll for a month.
        
        Args:
            month: "YYYY-MM" format
            
        Returns:
            Summary stats
        """
        # Parse month
        year, month_num = map(int, month.split("-"))
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        start = datetime(year, month_num, 1)
        end = start + relativedelta(months=1)
        
        records = self.db.query(PayrollRecord).filter(
            PayrollRecord.processing_date >= start,
            PayrollRecord.processing_date < end
        ).all()
        
        summary = {
            "month": month,
            "total_records": len(records),
            "total_amount": sum(r.amount for r in records),
            "approved_count": sum(1 for r in records if r.status == PayrollRecord.PaymentStatus.PROCESSED),
            "rejected_count": sum(1 for r in records if r.status == PayrollRecord.PaymentStatus.REJECTED),
            "pending_count": sum(1 for r in records if r.status == PayrollRecord.PaymentStatus.PENDING),
            "average_risk_score": sum(r.risk_score_at_time or 0 for r in records) / len(records) if records else 0,
            "by_status": {}
        }
        
        for status in PayrollRecord.PaymentStatus:
            count = sum(1 for r in records if r.status == status)
            summary["by_status"][status.value] = count
        
        return summary
