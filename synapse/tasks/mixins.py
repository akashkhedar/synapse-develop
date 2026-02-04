from core.feature_flags import flag_set


class TaskMixin:
    def has_permission(self, user: 'User') -> bool:  # noqa: F821
        """Called by Task#has_permission"""
        return True

    def _get_is_labeled_value(self) -> bool:
        if flag_set('fflag_fix_fit_1082_overlap_use_distinct_annotators', user='auto'):
            n = self.completed_annotations.values('completed_by').distinct().count()
        else:
            n = self.completed_annotations.count()
        return n >= self.overlap

    def update_is_labeled(self, *args, **kwargs) -> None:
        self.is_labeled = self._get_is_labeled_value()

    @classmethod
    def post_process_bulk_update_stats(cls, tasks) -> None:
        pass

    def before_delete_actions(self):
        """
        Actions to execute before task deletion
        """
        # Handle billing refund for single task deletion
        if hasattr(self, 'project') and self.project:
            try:
                from billing.services import ProjectBillingService
                
                refund_result = ProjectBillingService.refund_deleted_tasks(
                    self.project, 
                    [self.id]
                )
                
                if refund_result.get("success") and refund_result.get("refund_amount", 0) > 0:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Single task deletion refund: ₹{refund_result.get('refund_amount', 0)} "
                        f"refunded for task {self.id} in project {self.project.id}"
                    )
            except ImportError:
                # Billing module not available
                pass
            except Exception as exc:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing refund for deleted task {self.id}: {exc}")

    @staticmethod
    def after_bulk_delete_actions(tasks_ids, project):
        """
        Actions to execute after bulk task deletion
        """
        # Handle billing refunds for unannotated deleted tasks
        try:
            from billing.services import ProjectBillingService
            
            refund_result = ProjectBillingService.refund_deleted_tasks(project, tasks_ids)
            
            if refund_result.get("success") and refund_result.get("refund_amount", 0) > 0:
                from core.utils.common import logger
                logger.info(
                    f"Task deletion refund: {refund_result.get('tasks_refunded', 0)} "
                    f"tasks refunded ₹{refund_result.get('refund_amount', 0)} "
                    f"for project {project.id}"
                )
        except ImportError:
            # Billing module not available
            pass
        except Exception as exc:
            from core.utils.common import logger
            logger.error(f"Error processing refund for deleted tasks: {exc}")

    def get_rejected_query(self):
        pass


class AnnotationMixin:
    def has_permission(self, user: 'User') -> bool:  # noqa: F821
        """Called by Annotation#has_permission"""
        return True





