from uuid import UUID, uuid5

NAMESPACE = UUID("f59b2f3a-8300-4a7e-a9f4-e888ebc92f54")


class UUIDService:
    def project(self, project_name: str) -> UUID:
        return uuid5(NAMESPACE, f"project:{project_name}")

    def chapter(self, chapter_id: str) -> UUID:
        return uuid5(NAMESPACE, f"chapter:{chapter_id}")

    def quest(self, quest_id: str) -> UUID:
        return uuid5(NAMESPACE, f"quest:{quest_id}")

    def task(self, quest_id: str, task_id: str) -> UUID:
        return uuid5(NAMESPACE, f"task:{quest_id}:{task_id}")

    def reward(self, quest_id: str, reward_id: str) -> UUID:
        return uuid5(NAMESPACE, f"reward:{quest_id}:{reward_id}")
