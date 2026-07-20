from generator.builder import ChapterBuilder


def build_ae2_quantum_engineering(chapter: ChapterBuilder, mastery: str) -> str:
    plan = (
        chapter.quest(
            "quantum_plan",
            "Plan the Quantum Network",
            "ae2:quantum_ring",
            (
                "Design the next generation of your ME system: bulk storage, redundant channel routes, "
                "remote quantum links, spatial engineering, and crafting capacity large enough for endgame jobs."
            ),
            72,
            2,
            optional=True,
        )
        .depends_on(mastery)
        .checkmark()
        .finish()
    )

    bulk_cells = (
        chapter.quest(
            "bulk_storage_cells",
            "Storage in Bulk",
            "ae2:item_storage_cell_64k",
            "Build at least one 64k item storage cell for high-volume materials.",
            74,
            -3,
            optional=True,
        )
        .depends_on(plan)
        .item("ae2:item_storage_cell_64k")
        .finish()
    )

    dedicated_drives = (
        chapter.quest(
            "dedicated_drives",
            "Drives with a Purpose",
            "ae2:drive",
            (
                "Separate bulk materials, general storage, and automation buffers into clearly labeled ME Drives. "
                "A large network should be understandable at a glance."
            ),
            76,
            -3,
            optional=True,
        )
        .depends_on(bulk_cells)
        .checkmark()
        .finish()
    )

    overflow_control = (
        chapter.quest(
            "overflow_control",
            "No More Silent Overflow",
            "ae2:level_emitter",
            (
                "Add stock limits, overflow exports, or void-safe disposal to at least three bulk resources so "
                "one runaway process cannot fill the entire network."
            ),
            78,
            -3,
            optional=True,
        )
        .depends_on(dedicated_drives)
        .checkmark()
        .finish()
    )

    crafting_storage = (
        chapter.quest(
            "large_crafting_storage",
            "A Larger Crafting Brain",
            "ae2:crafting_storage_64k",
            "Build a 64k Crafting Storage block for larger autocrafting jobs.",
            74,
            0,
            optional=True,
        )
        .depends_on(plan)
        .item("ae2:crafting_storage_64k")
        .finish()
    )

    coprocessors = (
        chapter.quest(
            "coprocessor_array",
            "Parallel Assembly",
            "ae2:crafting_accelerator",
            (
                "Expand a crafting CPU with multiple co-processing units so independent crafting steps can run "
                "in parallel instead of waiting on one assembler at a time."
            ),
            76,
            0,
            optional=True,
        )
        .depends_on(crafting_storage)
        .checkmark()
        .finish()
    )

    bulk_patterns = (
        chapter.quest(
            "bulk_pattern_library",
            "A Library of Industry",
            "ae2:pattern_provider",
            "Encode and organize at least twenty useful crafting or processing patterns.",
            78,
            0,
            optional=True,
        )
        .depends_on(coprocessors)
        .checkmark()
        .finish()
    )

    complex_job = (
        chapter.quest(
            "complex_crafting_job",
            "The Hundred-Step Request",
            "ae2:crafting_monitor",
            (
                "Complete a large autocrafting request with many subcomponents and machine-processing steps. "
                "Review the crafting plan before starting and resolve any missing ingredients cleanly."
            ),
            80,
            0,
            optional=True,
        )
        .depends_on(bulk_patterns)
        .checkmark()
        .finish()
    )

    redundant_channels = (
        chapter.quest(
            "redundant_channels",
            "Route around Failure",
            "ae2:dense_smart_cable",
            (
                "Create a documented backup channel route or spare P2P path for a critical factory branch. "
                "A single broken cable should not disable the entire base."
            ),
            74,
            4,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    network_monitoring = (
        chapter.quest(
            "network_monitoring",
            "Watch the Network Breathe",
            "ae2:network_tool",
            (
                "Audit channel use, power draw, crafting CPUs, and storage pressure. Mark overloaded branches "
                "and leave room for future expansion."
            ),
            76,
            4,
            optional=True,
        )
        .depends_on(redundant_channels)
        .checkmark()
        .finish()
    )

    quantum_ring = (
        chapter.quest(
            "quantum_ring",
            "Build the Quantum Ring",
            "ae2:quantum_ring",
            "Construct a complete Quantum Network Bridge ring at the main base.",
            78,
            5,
            optional=True,
        )
        .depends_on(network_monitoring)
        .item("ae2:quantum_ring", 8)
        .finish()
    )

    singularity = (
        chapter.quest(
            "singularity",
            "Matter under Pressure",
            "ae2:singularity",
            "Produce a Singularity for quantum-link construction.",
            80,
            5,
            optional=True,
        )
        .depends_on(quantum_ring)
        .item("ae2:singularity")
        .finish()
    )

    entangled = (
        chapter.quest(
            "entangled_singularity",
            "Entangle the Pair",
            "ae2:quantum_entangled_singularity",
            "Create a matched pair of Quantum Entangled Singularities.",
            82,
            5,
            optional=True,
        )
        .depends_on(singularity)
        .item("ae2:quantum_entangled_singularity", 2)
        .finish()
    )

    remote_link = (
        chapter.quest(
            "remote_quantum_link",
            "One Network, Any Distance",
            "ae2:quantum_link",
            (
                "Complete a powered Quantum Network Bridge at a remote outpost and verify storage and channel "
                "access across the link."
            ),
            84,
            5,
            optional=True,
        )
        .depends_on(entangled)
        .checkmark()
        .finish()
    )

    spatial_io = (
        chapter.quest(
            "spatial_io",
            "Spatial Engineering",
            "ae2:spatial_io_port",
            "Craft a Spatial IO Port and study the power and cell requirements for spatial storage.",
            74,
            8,
            optional=True,
        )
        .depends_on(plan)
        .item("ae2:spatial_io_port")
        .finish()
    )

    spatial_pylons = (
        chapter.quest(
            "spatial_pylons",
            "Define the Volume",
            "ae2:spatial_pylon",
            "Build a valid Spatial Pylon frame around a small test chamber.",
            76,
            8,
            optional=True,
        )
        .depends_on(spatial_io)
        .item("ae2:spatial_pylon", 8)
        .finish()
    )

    spatial_test = (
        chapter.quest(
            "spatial_test",
            "Store a Room",
            "ae2:spatial_cell_component_2",
            (
                "Perform a controlled spatial-storage test with a small, nonessential structure. Confirm the "
                "chamber is empty of players and irreplaceable machines before activation."
            ),
            78,
            8,
            optional=True,
        )
        .depends_on(spatial_pylons)
        .checkmark()
        .finish()
    )

    recovery_drill = (
        chapter.quest(
            "network_recovery_drill",
            "Restore from a Network Failure",
            "ae2:energy_cell",
            (
                "Simulate a controller, power, or trunk-cable failure and restore essential storage and crafting "
                "access using your documented recovery plan."
            ),
            82,
            1,
            optional=True,
        )
        .depends_on(overflow_control, complex_job, network_monitoring)
        .checkmark()
        .finish()
    )

    remote_industry = (
        chapter.quest(
            "remote_industry",
            "Industry beyond the Horizon",
            "ae2:quantum_link",
            (
                "Operate a remote factory through the quantum link with controlled imports, exports, stock limits, "
                "and autocrafting support from the main network."
            ),
            86,
            4,
            optional=True,
        )
        .depends_on(remote_link, recovery_drill)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "quantum_mastery",
            "The Quantum Architect",
            "ae2:quantum_link",
            (
                "Your ME system now combines bulk storage, deep autocrafting, monitored redundancy, spatial "
                "engineering, and remote quantum networking into dependable endgame infrastructure."
            ),
            88,
            3,
            optional=True,
        )
        .depends_on(remote_industry, spatial_test)
        .checkmark()
        .reward_item("ae2:fluix_crystal", 32)
        .finish()
    )
