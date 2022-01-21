import asyncio as aio


class Sleeper:

    def __init__(self):
        self.tasks = set()

    async def sleep(self, delay, result=None):
        coro = aio.sleep(delay, result=result)
        task = aio.ensure_future(coro)
        self.tasks.add(task)
        try:
            return await task
        except aio.CancelledError:
            return result
        finally:
            self.tasks.remove(task)

    def cancel_all_helper(self):
        cancelled = set()
        for task in self.tasks:
            if task.cancel():
                cancelled.add(task)
        return cancelled

    async def cancel_all(self):
        cancelled = self.cancel_all_helper()
        await aio.wait(self.tasks)
        self.tasks -= cancelled
        return len(cancelled)
