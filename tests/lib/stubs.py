from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Union, Optional, BinaryIO, Dict, Tuple, Set

import toloka.client as toloka


class TolokaClientCallRecorderStub:
    def __init__(self):
        self.calls: List[Tuple[str, tuple]] = []

    def get_projects(self, status: str) -> List[toloka.Project]:
        self.calls.append(('get_projects', (status,)))
        return []

    def create_project(self, prj: toloka.Project) -> toloka.Project:
        self.calls.append(('create_project', (prj,)))
        return prj

    def update_project(self, project_id: str, prj: toloka.Project) -> toloka.Project:
        self.calls.append(('update_project', (project_id, prj)))
        return prj

    def patch_assignment(self, assignment_id: str, patch: toloka.assignment.AssignmentPatch):
        self.calls.append(('patch_assignment', (assignment_id, patch)))

    def patch_task_overlap_or_min(self, task_id: str, patch: toloka.task.TaskOverlapPatch):
        self.calls.append(('patch_task_overlap_or_min', (task_id, patch)))

    def create_pool(self, pool: toloka.Pool) -> toloka.Pool:
        self.calls.append(('create_pool', (pool,)))
        return pool

    def open_pool(self, pool_id: str):
        self.calls.append(('open_pool', (pool_id,)))

    def create_tasks(self, tasks, *args, **kwargs):
        self.calls.append(('create_tasks', (tasks,)))

    def create_user_bonuses_async(
        self,
        bonuses: List[toloka.user_bonus.UserBonus],
    ) -> toloka.operations.UserBonusCreateBatchOperation:
        self.calls.append(('create_user_bonuses_async', (bonuses,)))
        return toloka.operations.UserBonusCreateBatchOperation()

    def wait_operation(self, op: toloka.operations.Operation) -> toloka.operations.Operation:
        self.calls.append(('wait_operation', (op,)))
        op.status = toloka.operations.Operation.Status.SUCCESS
        return op

    def set_user_restriction(self, user_restriction: toloka.user_restriction.UserRestriction):
        self.calls.append(('set_user_restriction', (user_restriction,)))

    def get_requester(self):
        self.calls.append(('get_requester', ()))

    def get_skills(self, name: str):
        self.calls.append(('get_skills', (name,)))

    def create_task(self, task: toloka.Task):
        self.calls.append(('create_task', (task,)))

    def get_assignments(self, pool_id: str, status: List[toloka.Assignment.Status]):
        self.calls.append(('get_assignments', (pool_id, status)))

    def accept_assignment(self, assignment_id: str, public_comment: str):
        self.calls.append(('accept_assignment', (assignment_id, public_comment)))

    def reject_assignment(self, assignment_id: str, public_comment: str):
        self.calls.append(('reject_assignment', (assignment_id, public_comment)))

    def create_skill(self, name: str, hidden: bool):
        self.calls.append(('create_skill', (name, hidden)))

    def get_pool(self, pool_id: str):
        self.calls.append(('get_pool', (pool_id,)))

    def get_pools(self, project_id: str, status: str):
        self.calls.append(('get_pools', (project_id, status)))

    def create_training(self, training: toloka.Training) -> toloka.Training:
        self.calls.append(('create_training', (training,)))
        return training

    def find_trainings(
        self,
        project_id: str,
        status: toloka.Training.Status,
        sort: toloka.search_requests.TrainingSortItems,
        limit: Optional[int],
    ):
        self.calls.append(('find_trainings', (project_id, status, sort, limit)))

    def open_training(self, training_id: str):
        self.calls.append(('open_training', (training_id,)))

    def get_attachment(self, attachment_id: str):
        self.calls.append(('get_attachment', (attachment_id,)))

    def download_attachment(self, attachment_id: str, out: BinaryIO):
        self.calls.append(('download_attachment', (attachment_id,)))  # skip 'out', can't compare it correctly

    def compose_message_thread(
        self,
        topic: str,
        text: str,
        recipients_select_type: Union[toloka.message_thread.RecipientsSelectType, str, None],
        recipients_filter: Optional[toloka.filter.FilterCondition],
        answerable: bool,
    ):
        self.calls.append(
            ('compose_message_thread', (topic, text, recipients_select_type, recipients_filter, answerable))
        )


class TolokaClientIntegrationStub(TolokaClientCallRecorderStub):
    id_to_project: Dict[str, toloka.Project]
    id_to_pool: Dict[str, toloka.Pool]
    id_to_assignment: Dict[str, toloka.Assignment]
    assignments_with_statuses: Set[str]
    tasks: List[toloka.Task]

    def __init__(self, assignments: List[toloka.Assignment], projects: List[toloka.Project]):
        self.id_to_project = {project.id: project for project in projects}
        self.id_to_pool = {}
        self.id_to_assignment = {assignment.id: assignment for assignment in assignments}
        self.assignments_with_statuses = set()
        self.tasks = []
        super(TolokaClientIntegrationStub, self).__init__()

    def get_project(self, project_id: str) -> toloka.Project:
        return self.id_to_project[project_id]

    def create_pool(self, pool: toloka.Pool) -> toloka.Pool:
        pool.id = pool.private_name
        pool.created = datetime.now()
        pool.last_stopped = pool.created + timedelta(hours=1)
        pool.is_closed = lambda: True
        pool = super(TolokaClientIntegrationStub, self).create_pool(pool)
        assert pool.id not in self.id_to_pool
        self.id_to_pool[pool.id] = pool
        return pool

    def get_pool(self, pool_id: str) -> toloka.Pool:
        return self.id_to_pool[pool_id]

    def patch_assignment(self, assignment_id: str, patch: toloka.assignment.AssignmentPatch):
        assert assignment_id not in self.assignments_with_statuses
        self.id_to_assignment[assignment_id].status = patch.status
        self.assignments_with_statuses.add(assignment_id)
        super(TolokaClientIntegrationStub, self).patch_assignment(assignment_id, patch)

    def create_tasks(self, tasks, *args, **kwargs):
        for i, task in enumerate(tasks):
            # emulate task ID assignment like in API
            task.id = f'task {str(i + len(self.tasks))}'
        self.tasks += tasks
        super(TolokaClientIntegrationStub, self).create_tasks(tasks, *args, **kwargs)

    def get_tasks(self, pool_id: str) -> List[toloka.Task]:
        return [task for task in self.tasks if task.pool_id == pool_id]


class Boto3SessionStub:
    @dataclass
    class Client:
        calls: List[Tuple[str, dict]] = field(default_factory=list)

        def put_object(self, **kwargs):
            del kwargs['Body']  # skip 'Body', can't compare it correctly
            self.calls.append(('put_object', kwargs))

    def client(self, **kwargs) -> 'Boto3SessionStub.Client':
        return self.Client()
