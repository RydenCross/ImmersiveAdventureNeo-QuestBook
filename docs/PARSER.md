# FTB Quests v13 Parser

`FTBQuestParser` loads `data.snbt`, localization, and every chapter into the core model.

The parser preserves each original compound in `raw_data`, allowing the future writer to round-trip fields the SDK does not yet understand.

FTB's 16-character hexadecimal IDs are retained as `ftb_id` and mapped to Python `UUID` objects without changing their numeric value.
