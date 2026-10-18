from .schemas import TaskRecord
#前面的下划线 _ 表示这是一个内部私有变量，别人别随便动。
#：这是类型注解。它在告诉你：“这个仓库是一个字典（dict）”。
_tasks: dict[str, TaskRecord] = {}
#保存
#我这个函数执行完之后，不会返回任何有价值的数据
def save_task(task: TaskRecord) -> None:
    _tasks[task.task_id] = task

#查询
def get_task(task_id: str) -> TaskRecord | None:
    return _tasks.get(task_id)
