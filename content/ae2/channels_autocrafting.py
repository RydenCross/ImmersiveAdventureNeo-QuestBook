from generator.builder import ChapterBuilder


def build_ae2_channels_autocrafting(
    chapter: ChapterBuilder, foundations_complete: str
) -> str:
    channels = (
        chapter.quest(
            "channels",
            "Count the Channels",
            "ae2:smart_cable",
            (
                "Most AE2 devices consume one channel. Standard cables carry eight channels, while "
                "dense cables can carry thirty-two. Learn to plan branches before expanding the network."
            ),
            26,
            0,
        )
        .depends_on(foundations_complete)
        .checkmark()
        .finish()
    )

    smart_cable = (
        chapter.quest(
            "smart_cable",
            "See the Network Think",
            "ae2:smart_cable",
            "Craft Smart Cable so channel usage is visible directly on the cable.",
            28,
            -2,
        )
        .depends_on(channels)
        .item("ae2:smart_cable", 8)
        .finish()
    )

    dense_cable = (
        chapter.quest(
            "dense_smart_cable",
            "Thirty-Two Lanes",
            "ae2:dense_smart_cable",
            (
                "Craft Dense Smart Cable for high-capacity trunks. Dense cable carries thirty-two "
                "channels but cannot directly host buses or terminals."
            ),
            30,
            -2,
        )
        .depends_on(smart_cable)
        .item("ae2:dense_smart_cable", 4)
        .finish()
    )

    anchors = (
        chapter.quest(
            "cable_anchors",
            "Separate the Branches",
            "ae2:cable_anchor",
            (
                "Craft Cable Anchors. They prevent neighboring cables from connecting and help keep "
                "channel routes intentional and readable."
            ),
            30,
            -4,
            optional=True,
        )
        .depends_on(smart_cable)
        .item("ae2:cable_anchor", 8)
        .finish()
    )

    interface = (
        chapter.quest(
            "interface",
            "Stock What Machines Need",
            "ae2:interface",
            (
                "Craft an ME Interface. Interfaces can expose network inventory and maintain a stock of "
                "selected items for machines or subnetworks."
            ),
            30,
            1.5,
        )
        .depends_on(channels)
        .item("ae2:interface")
        .finish()
    )

    blank_pattern = (
        chapter.quest(
            "blank_pattern",
            "Instructions Await",
            "ae2:blank_pattern",
            "Craft Blank Patterns, the reusable media that store crafting and processing instructions.",
            32,
            1.5,
        )
        .depends_on(interface)
        .item("ae2:blank_pattern", 8)
        .finish()
    )

    encoding_terminal = (
        chapter.quest(
            "pattern_encoding_terminal",
            "Teach the Network",
            "ae2:pattern_encoding_terminal",
            (
                "Craft an ME Pattern Encoding Terminal to encode crafting, processing, smithing, and "
                "stonecutting patterns from the network interface."
            ),
            34,
            1.5,
        )
        .depends_on(blank_pattern)
        .item("ae2:pattern_encoding_terminal")
        .finish()
    )

    crafting_pattern = (
        chapter.quest(
            "crafting_pattern",
            "Encode a Crafting Pattern",
            "ae2:crafting_pattern",
            "Encode a simple crafting-table recipe that you use often.",
            36,
            0,
        )
        .depends_on(encoding_terminal)
        .item("ae2:crafting_pattern")
        .finish()
    )

    processing_pattern = (
        chapter.quest(
            "processing_pattern",
            "Describe a Machine Process",
            "ae2:processing_pattern",
            (
                "Encode a processing pattern for a furnace or modded machine. Processing patterns define "
                "inputs and expected outputs without caring how the machine performs the work."
            ),
            36,
            3,
        )
        .depends_on(encoding_terminal)
        .item("ae2:processing_pattern")
        .finish()
    )

    provider = (
        chapter.quest(
            "pattern_provider",
            "Provide the Ingredients",
            "ae2:pattern_provider",
            (
                "Craft a Pattern Provider. It stores encoded patterns and pushes complete ingredient "
                "batches into adjacent machines when a crafting job requests them."
            ),
            38,
            1.5,
        )
        .depends_on(crafting_pattern, processing_pattern)
        .item("ae2:pattern_provider")
        .finish()
    )

    assembler = (
        chapter.quest(
            "molecular_assembler",
            "Automated Crafting Table",
            "ae2:molecular_assembler",
            (
                "Craft a Molecular Assembler and place it beside a Pattern Provider. Together they can "
                "perform encoded crafting-table recipes automatically."
            ),
            40,
            0,
        )
        .depends_on(provider)
        .item("ae2:molecular_assembler")
        .finish()
    )

    crafting_unit = (
        chapter.quest(
            "crafting_unit",
            "Build a Crafting CPU",
            "ae2:crafting_unit",
            (
                "Craft a Crafting Unit, the structural block used to assemble an AE2 crafting CPU "
                "multiblock."
            ),
            38,
            -2,
        )
        .depends_on(crafting_pattern, dense_cable)
        .item("ae2:crafting_unit")
        .finish()
    )

    crafting_storage = (
        chapter.quest(
            "crafting_storage",
            "Memory for the Job",
            "ae2:crafting_storage_1k",
            (
                "Craft 1k Crafting Storage. Every crafting CPU needs storage for ingredients and "
                "intermediate results while a job is running."
            ),
            40,
            -2,
        )
        .depends_on(crafting_unit)
        .item("ae2:crafting_storage_1k")
        .finish()
    )

    coprocessor = (
        chapter.quest(
            "crafting_accelerator",
            "Work in Parallel",
            "ae2:crafting_accelerator",
            (
                "Add a Crafting Co-Processing Unit so the CPU can dispatch additional crafting steps "
                "and ingredient batches in parallel."
            ),
            42,
            -3,
            optional=True,
        )
        .depends_on(crafting_storage)
        .item("ae2:crafting_accelerator")
        .finish()
    )

    monitor = (
        chapter.quest(
            "crafting_monitor",
            "Watch the Job",
            "ae2:crafting_monitor",
            "Add a Crafting Monitor to display the active job handled by a crafting CPU.",
            42,
            -1,
            optional=True,
        )
        .depends_on(crafting_storage)
        .item("ae2:crafting_monitor")
        .finish()
    )

    cpu_online = (
        chapter.quest(
            "cpu_online",
            "Bring the CPU Online",
            "ae2:crafting_storage_1k",
            (
                "Assemble a valid crafting CPU multiblock containing crafting storage and connect it "
                "to the ME network."
            ),
            44,
            -2,
        )
        .depends_on(crafting_storage)
        .checkmark()
        .finish()
    )

    first_craft = (
        chapter.quest(
            "first_autocraft",
            "Request the First Autocraft",
            "ae2:molecular_assembler",
            (
                "Place a crafting pattern in a Pattern Provider beside a Molecular Assembler, then "
                "request the item from a terminal and let the network complete the job."
            ),
            44,
            0,
        )
        .depends_on(assembler, cpu_online)
        .checkmark()
        .finish()
    )

    machine_autocraft = (
        chapter.quest(
            "machine_autocraft",
            "Automate a Machine Recipe",
            "ae2:pattern_provider",
            (
                "Use a processing pattern and Pattern Provider to automate a furnace or another machine. "
                "Ensure the finished product re-enters the ME network."
            ),
            44,
            2,
        )
        .depends_on(provider, cpu_online)
        .checkmark()
        .finish()
    )

    recursive = (
        chapter.quest(
            "multi_step_craft",
            "A Recipe with Prerequisites",
            "ae2:calculation_processor",
            (
                "Encode a multi-step item whose ingredients must also be autocrafted. Confirm that the "
                "crafting CPU schedules the prerequisites before the final recipe."
            ),
            46,
            0,
        )
        .depends_on(first_craft, machine_autocraft)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "autocrafting_complete",
            "The Network Crafts for You",
            "ae2:pattern_encoding_terminal",
            (
                "Your ME network now routes channels visibly, stores patterns, runs a crafting CPU, and "
                "automates both crafting-table and machine recipes."
            ),
            48,
            0,
        )
        .depends_on(recursive)
        .checkmark()
        .reward_item("minecraft:quartz", 32)
        .finish()
    )
