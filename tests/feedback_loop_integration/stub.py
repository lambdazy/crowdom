import itertools
from typing import List, Union

import toloka.client as toloka

from .data import markup_pool_id, check_pool_id
from .. import lib


class TolokaClientStub(lib.TolokaClientIntegrationStub):
    markup_assignments_by_iterations: List[List[toloka.Assignment]]
    markup_assignments_requests: int
    check_assignments_by_iterations: List[List[toloka.Assignment]]
    check_assignments_requests: int
    has_model_markup: bool

    def __init__(
        self,
        markup_assignments_by_iterations,
        check_assignments_by_iterations,
        markup_project: toloka.Project,
        check_project: toloka.Project,
        has_model_markup: bool = False,
    ):
        self.url = 'https://toloka.com'
        self.markup_assignments_by_iterations = markup_assignments_by_iterations
        self.markup_assignments_requests = 0
        self.check_assignments_by_iterations = check_assignments_by_iterations
        self.check_assignments_requests = 0
        self.markup_assignments = []
        self.check_assignments = []
        self.has_model_markup = has_model_markup
        super(TolokaClientStub, self).__init__(
            list(itertools.chain(*markup_assignments_by_iterations))
            + list(itertools.chain(*check_assignments_by_iterations)),
            [markup_project, check_project],
        )

    # Emulation of task execution by workers. The logic of this method strongly depends on the current implementation
    # of feedback loop.
    def get_assignments(
        self,
        status: Union[toloka.Assignment.Status, List[toloka.Assignment.Status]],
        pool_id: str,
    ) -> List[toloka.Assignment]:
        if not isinstance(status, list):
            status = [status]
        if pool_id == markup_pool_id:
            loop_iteration = self.markup_assignments_requests
            if loop_iteration < len(self.markup_assignments_by_iterations):
                self.markup_assignments += self.markup_assignments_by_iterations[loop_iteration]
            self.markup_assignments_requests += 1
            return self.markup_assignments
        elif pool_id == check_pool_id:
            if status == [toloka.Assignment.SUBMITTED]:
                # Each annotation loop iterations contains two calls to get checks from evaluation loop. Each call to
                # evaluation loop contains three calls to get_assignments(), plus another call to generate aggregated
                # evaluations, resulting in four calls to get_assignments() overall to each evaluation loop call.
                #
                # First evaluation loop call is needed for the case of restarting @op, at the time of this call, new
                # tasks for checks have not yet been created.
                #
                # Second evaluation loop call happens after the creation of new evaluation tasks, so the SUBMITTED
                # assignments are returned only on this call.
                #
                # If there is a `markup model`, another call to receive evaluations is added, which happens before the
                # first two calls.
                #
                # Additional calls to receive checks are happening in subsequent actions after annotation loop, like
                # giving bonuses and getting results, in this case there are also not new assignments.

                requests_per_get_checks = 4
                get_checks_per_markup_iteration = 3 if self.has_model_markup else 2

                requests_per_markup_iteration = requests_per_get_checks * get_checks_per_markup_iteration

                new_check_tasks_appear_after = requests_per_markup_iteration - requests_per_get_checks
                markup_loop_finishes_after = len(self.check_assignments_by_iterations) * requests_per_markup_iteration

                if (
                    self.check_assignments_requests % requests_per_markup_iteration < new_check_tasks_appear_after
                    or self.check_assignments_requests >= markup_loop_finishes_after
                ):
                    assignments = []
                else:
                    loop_iteration = self.check_assignments_requests // requests_per_markup_iteration
                    assignments = self.check_assignments_by_iterations[loop_iteration]
            else:
                # No linked to iteration, since we get all ACCEPTED/REJECTED assignments existing at the moment.
                assignments = [
                    assignment
                    for assignment in self.id_to_assignment.values()
                    if assignment.id.startswith('check') and assignment.status in status
                ]
            self.check_assignments_requests += 1
            return assignments
