# FTB Quests v13 Writer

`FTBQuestWriter` serializes the domain model into an FTB Quests directory.

```python
from generator.parser import FTBQuestParser
from generator.writer import FTBQuestWriter

project = FTBQuestParser().load("config/ftbquests")
project.get_quest("65919EFE1A013093").title = "A New Beginning"
FTBQuestWriter().write(project, "build/ftbquests")
```

Known FTB fields are updated from the models. Unknown fields retained in
`raw_data` are carried forward, which protects mod-specific task data.
