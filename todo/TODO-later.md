# Tasks for Later

## Payment & Contract Completion

### Release Assets After Completing Contract
- [ ] After `complete_contract` is called and contract is marked as completed, implement actual payment release logic
- [ ] Release pre-approved payments/assets to selected workers who have completed their work
- [ ] This should happen after the contract is completed but before marking the job as complete
- [ ] Integrate with Interledger payment service to actually release the escrowed funds
- [ ] Update payment status for each worker who receives payment
- [ ] Send notifications to workers when payments are released

Note: Currently `complete_contract` is a stub that only marks `contract_completed=True`. The actual payment release functionality needs to be implemented.


[] add validation for the payments on contract creation and compleation that the seller gets the money using their key
[] where it says Entregables: Audio we should also have icons what video.png  if there we need more icons for this