# Core Models

The domain model is independent of FTB Quests SNBT.

## Object hierarchy

- `Project`
  - `Chapter`
    - `Quest`
      - `Task`
      - `Reward`
      - `Dependency`
      - `Position`

`generator.ids.UUIDService` provides deterministic UUID5 identifiers so repeated builds keep stable IDs.
