def publish_workflow_state(workflow_state):
    # publish the Page associated with a WorkflowState
    if workflow_state.current_task_state:
        workflow_state.current_task_state.page_revision.publish()
    else:
        workflow_state.page.get_latest_revision().publish()
