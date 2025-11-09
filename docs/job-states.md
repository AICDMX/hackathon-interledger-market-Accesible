# Job States

Jobs progress through a defined lifecycle. Each state is represented by a single-word identifier:

| State | Identifier | Definition |
| --- | --- | --- |
| **Draft** | `draft` | Job is being created or edited by the funder, not yet published or visible to submitters. |
| **Recruiting** | `recruiting` | Job is published and actively seeking sellers/submitters to apply with their profiles. Applications are being collected. |
| **Selecting** | `selecting` | Job owner is reviewing applications and selecting which submitters to approve. Waiting for confirmation/selections of submitters. |
| **Submitting** | `submitting` | Selected submitters have been confirmed and are working on their submissions. Waiting for submissions to be completed. |
| **Reviewing** | `reviewing` | Submissions have been received and are awaiting confirmation/acceptance by the job owner. Waiting for confirmation of submissions. |
| **Expired** | `expired` | Job deadline has passed or the job was cancelled before completion. No further actions can be taken. |
| **Canceled** | `canceled` | Job has been manually canceled by the funder. No further actions can be taken. |
| **Complete** | `complete` | All required submissions have been accepted and the job is finished. Payments have been processed. |

## State Transitions

- Jobs start as `draft` when created
- `draft` ? `recruiting` when published
- `recruiting` ? `selecting` when applications are closed or funder begins selection
- `selecting` ? `submitting` when submitters are confirmed
- `submitting` ? `reviewing` when submissions are received
- `reviewing` ? `complete` when all submissions are accepted
- Any active state ? `canceled` when funder cancels the contract
- Any state ? `expired` if deadline passes or job is cancelled

## Notes

- The `funded` state has been removed. Funding status is now tracked separately via the `is_funded` flag and `funded_amount` field, independent of job state.
- Jobs in `recruiting` state are visible in the browse jobs list and accept applications.
- Jobs in `submitting` state accept work submissions from selected submitters.
- Jobs in `reviewing` state are waiting for the funder to accept/reject submissions.
- Jobs can be canceled from any active state (`draft`, `recruiting`, `selecting`, `submitting`, `reviewing`) but not from `complete`, `canceled`, or `expired`.
- Canceled jobs cannot be reactivated or modified.
