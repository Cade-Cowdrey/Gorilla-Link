"""
Data Governance Service
Data lineage tracking, quality monitoring, retention policies, and bias detection
"""

from typing import Dict, Any, List, Optional
from extensions import db
from models_extended import DataLineage, BiasMonitoring, DataRetention
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class DataGovernanceService:
    """Manage data quality, lineage, and compliance"""
    
    # ============================================================
    # DATA LINEAGE
    # ============================================================
    
    def track_lineage(
        self,
        entity_type: str,
        entity_id: int,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        transformation: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Track data lineage - where data came from and how it was transformed
        """
        try:
            lineage = DataLineage(
                entity_type=entity_type,
                entity_id=entity_id,
                source_type=source_type,
                source_id=source_id,
                transformation=transformation,
                metadata=metadata or {}
            )
            
            db.session.add(lineage)
            db.session.commit()
            
            logger.info(f"Data lineage tracked: {entity_type}:{entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Data lineage tracking error: {e}")
            db.session.rollback()
            return False
    
    def get_lineage_chain(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        """
        Get complete lineage chain for an entity
        """
        try:
            chain = []
            current_type = entity_type
            current_id = entity_id
            
            # Traverse backwards up to 10 levels
            for _ in range(10):
                lineage = DataLineage.query.filter_by(
                    entity_type=current_type,
                    entity_id=current_id
                ).first()
                
                if not lineage:
                    break
                
                chain.append({
                    "entity_type": lineage.entity_type,
                    "entity_id": lineage.entity_id,
                    "source_type": lineage.source_type,
                    "source_id": lineage.source_id,
                    "transformation": lineage.transformation,
                    "created_at": lineage.created_at.isoformat(),
                    "metadata": lineage.metadata
                })
                
                # Move to source
                if lineage.source_type and lineage.source_id:
                    current_type = lineage.source_type
                    current_id = lineage.source_id
                else:
                    break
            
            return chain
            
        except Exception as e:
            logger.error(f"Lineage chain error: {e}")
            return []
    
    def get_lineage_graph(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """
        Get lineage as a graph structure for visualization
        """
        try:
            chain = self.get_lineage_chain(entity_type, entity_id)
            
            nodes = []
            edges = []
            
            for i, item in enumerate(chain):
                node_id = f"{item['entity_type']}:{item['entity_id']}"
                nodes.append({
                    "id": node_id,
                    "type": item['entity_type'],
                    "entity_id": item['entity_id'],
                    "transformation": item.get('transformation')
                })
                
                if item['source_type'] and item['source_id']:
                    source_id = f"{item['source_type']}:{item['source_id']}"
                    edges.append({
                        "from": source_id,
                        "to": node_id,
                        "transformation": item.get('transformation')
                    })
            
            return {
                "nodes": nodes,
                "edges": edges
            }
            
        except Exception as e:
            logger.error(f"Lineage graph error: {e}")
            return {"nodes": [], "edges": []}
    
    # ============================================================
    # BIAS MONITORING
    # ============================================================
    
    def detect_bias(
        self,
        model_name: str,
        prediction_type: str,
        demographic_group: str,
        true_positives: int,
        false_positives: int,
        true_negatives: int,
        false_negatives: int
    ) -> Dict[str, Any]:
        """
        Detect bias in ML model predictions
        Calculate fairness metrics
        """
        try:
            # Calculate metrics
            total = true_positives + false_positives + true_negatives + false_negatives
            
            if total == 0:
                return {"error": "No data points"}
            
            accuracy = (true_positives + true_negatives) / total
            
            # Precision
            precision_denom = true_positives + false_positives
            precision = true_positives / precision_denom if precision_denom > 0 else 0
            
            # Recall (True Positive Rate)
            recall_denom = true_positives + false_negatives
            recall = true_positives / recall_denom if recall_denom > 0 else 0
            
            # False Positive Rate
            fpr_denom = false_positives + true_negatives
            false_positive_rate = false_positives / fpr_denom if fpr_denom > 0 else 0
            
            # F1 Score
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # Store bias metrics
            bias_record = BiasMonitoring(
                model_name=model_name,
                prediction_type=prediction_type,
                demographic_group=demographic_group,
                true_positives=true_positives,
                false_positives=false_positives,
                true_negatives=true_negatives,
                false_negatives=false_negatives,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                false_positive_rate=false_positive_rate,
                f1_score=f1
            )
            
            db.session.add(bias_record)
            db.session.commit()
            
            result = {
                "model": model_name,
                "demographic_group": demographic_group,
                "metrics": {
                    "accuracy": round(accuracy, 4),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1_score": round(f1, 4),
                    "false_positive_rate": round(false_positive_rate, 4)
                },
                "confusion_matrix": {
                    "true_positives": true_positives,
                    "false_positives": false_positives,
                    "true_negatives": true_negatives,
                    "false_negatives": false_negatives
                }
            }
            
            logger.info(f"Bias detected for {model_name} - {demographic_group}")
            return result
            
        except Exception as e:
            logger.error(f"Bias detection error: {e}")
            db.session.rollback()
            return {"error": str(e)}
    
    def compare_bias_across_groups(self, model_name: str) -> Dict[str, Any]:
        """
        Compare bias metrics across demographic groups
        """
        try:
            records = BiasMonitoring.query.filter_by(
                model_name=model_name
            ).order_by(BiasMonitoring.created_at.desc()).limit(100).all()
            
            groups = {}
            for record in records:
                group = record.demographic_group
                if group not in groups:
                    groups[group] = {
                        "accuracy": [],
                        "precision": [],
                        "recall": [],
                        "f1_score": [],
                        "fpr": []
                    }
                
                groups[group]["accuracy"].append(record.accuracy)
                groups[group]["precision"].append(record.precision)
                groups[group]["recall"].append(record.recall)
                groups[group]["f1_score"].append(record.f1_score)
                groups[group]["fpr"].append(record.false_positive_rate)
            
            # Calculate averages
            comparison = {}
            for group, metrics in groups.items():
                comparison[group] = {
                    "avg_accuracy": sum(metrics["accuracy"]) / len(metrics["accuracy"]),
                    "avg_precision": sum(metrics["precision"]) / len(metrics["precision"]),
                    "avg_recall": sum(metrics["recall"]) / len(metrics["recall"]),
                    "avg_f1": sum(metrics["f1_score"]) / len(metrics["f1_score"]),
                    "avg_fpr": sum(metrics["fpr"]) / len(metrics["fpr"]),
                    "sample_count": len(metrics["accuracy"])
                }
            
            # Check for disparate impact
            disparate_impact = self._calculate_disparate_impact(comparison)
            
            return {
                "model": model_name,
                "groups": comparison,
                "disparate_impact": disparate_impact,
                "fairness_assessment": self._assess_fairness(disparate_impact)
            }
            
        except Exception as e:
            logger.error(f"Bias comparison error: {e}")
            return {"error": str(e)}
    
    def _calculate_disparate_impact(self, comparison: Dict) -> Dict[str, Any]:
        """Calculate disparate impact ratio"""
        if len(comparison) < 2:
            return {"warning": "Need at least 2 groups for comparison"}
        
        groups = list(comparison.keys())
        baseline_group = groups[0]
        baseline_metrics = comparison[baseline_group]
        
        impacts = {}
        for group in groups[1:]:
            group_metrics = comparison[group]
            
            # Disparate Impact = (Group Selection Rate) / (Baseline Selection Rate)
            # Using recall (TPR) as proxy for selection rate
            if baseline_metrics["avg_recall"] > 0:
                ratio = group_metrics["avg_recall"] / baseline_metrics["avg_recall"]
            else:
                ratio = 0
            
            impacts[f"{group}_vs_{baseline_group}"] = {
                "ratio": round(ratio, 4),
                "passes_80_rule": ratio >= 0.8  # 80% rule for disparate impact
            }
        
        return impacts
    
    def _assess_fairness(self, disparate_impact: Dict) -> str:
        """Assess overall fairness"""
        if "warning" in disparate_impact:
            return "insufficient_data"
        
        all_pass = all(
            impact["passes_80_rule"] 
            for impact in disparate_impact.values()
        )
        
        if all_pass:
            return "fair"
        else:
            return "potential_bias_detected"
    
    # ============================================================
    # DATA RETENTION
    # ============================================================
    
    def set_retention_policy(
        self,
        entity_type: str,
        retention_days: int,
        deletion_method: str = "soft",
        legal_basis: Optional[str] = None
    ) -> bool:
        """
        Set data retention policy for an entity type
        """
        try:
            # Check if policy exists
            policy = DataRetention.query.filter_by(entity_type=entity_type).first()
            
            if policy:
                policy.retention_days = retention_days
                policy.deletion_method = deletion_method
                policy.legal_basis = legal_basis
                policy.updated_at = datetime.utcnow()
            else:
                policy = DataRetention(
                    entity_type=entity_type,
                    retention_days=retention_days,
                    deletion_method=deletion_method,
                    legal_basis=legal_basis
                )
                db.session.add(policy)
            
            db.session.commit()
            
            logger.info(f"Retention policy set for {entity_type}: {retention_days} days")
            return True
            
        except Exception as e:
            logger.error(f"Retention policy error: {e}")
            db.session.rollback()
            return False
    
    def get_retention_policy(self, entity_type: str) -> Optional[DataRetention]:
        """Get retention policy for entity type"""
        return DataRetention.query.filter_by(entity_type=entity_type).first()
    
    def get_all_policies(self) -> List[DataRetention]:
        """Get all retention policies"""
        return DataRetention.query.all()
    
    def check_expiration(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Check which records should be deleted based on retention policy
        """
        try:
            policy = self.get_retention_policy(entity_type)
            if not policy:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
            
            # This is a generic query - in production, would need table-specific logic
            # Example for PageView:
            if entity_type == "PageView":
                from models import PageView
                expired = PageView.query.filter(
                    PageView.timestamp < cutoff_date
                ).all()
                
                return [{
                    "id": record.id,
                    "created": record.timestamp.isoformat(),
                    "age_days": (datetime.utcnow() - record.timestamp).days
                } for record in expired]
            
            return []
            
        except Exception as e:
            logger.error(f"Expiration check error: {e}")
            return []
    
    def apply_retention_policy(self, entity_type: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Apply retention policy - delete expired records
        """
        try:
            expired = self.check_expiration(entity_type)
            
            if dry_run:
                return {
                    "dry_run": True,
                    "entity_type": entity_type,
                    "expired_count": len(expired),
                    "records": expired[:10]  # Show first 10
                }
            
            policy = self.get_retention_policy(entity_type)
            deleted_count = 0
            
            if entity_type == "PageView":
                from models import PageView
                cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
                
                if policy.deletion_method == "hard":
                    # Hard delete
                    deleted_count = PageView.query.filter(
                        PageView.timestamp < cutoff_date
                    ).delete()
                else:
                    # Soft delete - would need a deleted_at column
                    logger.warning(f"Soft delete not implemented for {entity_type}")
            
            db.session.commit()
            
            logger.info(f"Applied retention policy for {entity_type}: {deleted_count} records deleted")
            
            return {
                "dry_run": False,
                "entity_type": entity_type,
                "deleted_count": deleted_count,
                "policy": {
                    "retention_days": policy.retention_days,
                    "deletion_method": policy.deletion_method
                }
            }
            
        except Exception as e:
            logger.error(f"Retention policy application error: {e}")
            db.session.rollback()
            return {"error": str(e)}
    
    # ============================================================
    # DATA QUALITY
    # ============================================================
    
    def check_data_quality(self, entity_type: str) -> Dict[str, Any]:
        """
        Run data quality checks
        """
        try:
            results = {
                "entity_type": entity_type,
                "checks": []
            }
            
            # Example quality checks for User
            if entity_type == "User":
                from models import User
                
                # Check for missing required fields
                missing_email = User.query.filter(
                    (User.email == None) | (User.email == '')
                ).count()
                
                # Check for duplicate emails
                duplicate_query = text("""
                    SELECT email, COUNT(*) as cnt 
                    FROM "user" 
                    WHERE email IS NOT NULL 
                    GROUP BY email 
                    HAVING COUNT(*) > 1
                """)
                duplicates = db.session.execute(duplicate_query).fetchall()
                
                # Check for invalid data formats
                invalid_phone = User.query.filter(
                    User.phone.isnot(None),
                    ~User.phone.op('~')(r'^\+?[0-9]{10,15}$')
                ).count()
                
                results["checks"] = [
                    {
                        "check": "missing_email",
                        "status": "pass" if missing_email == 0 else "fail",
                        "count": missing_email
                    },
                    {
                        "check": "duplicate_email",
                        "status": "pass" if len(duplicates) == 0 else "fail",
                        "count": len(duplicates)
                    },
                    {
                        "check": "invalid_phone",
                        "status": "pass" if invalid_phone == 0 else "fail",
                        "count": invalid_phone
                    }
                ]
            
            results["overall_status"] = "pass" if all(
                check["status"] == "pass" 
                for check in results["checks"]
            ) else "fail"
            
            return results
            
        except Exception as e:
            logger.error(f"Data quality check error: {e}")
            return {"error": str(e)}


# Singleton
_data_governance_service = None

def get_data_governance_service() -> DataGovernanceService:
    global _data_governance_service
    if _data_governance_service is None:
        _data_governance_service = DataGovernanceService()
    return _data_governance_service
