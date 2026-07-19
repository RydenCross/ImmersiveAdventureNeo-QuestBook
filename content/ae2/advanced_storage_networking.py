from generator.builder import ChapterBuilder


def build_ae2_advanced_storage_networking(
    chapter: ChapterBuilder, autocrafting_complete: str
) -> str:
    larger_cells = (
        chapter.quest(
            "larger_storage_cells",
            "Storage That Scales",
            "ae2:item_storage_cell_4k",
            (
                "Upgrade beyond the starter 1k cell. Larger cells hold more bytes, but every cell still "
                "has a type limit, so capacity and organization must be planned together."
            ),
            50,
            0,
        )
        .depends_on(autocrafting_complete)
        .item("ae2:item_storage_cell_4k")
        .finish()
    )

    storage_components = (
        chapter.quest(
            "storage_components",
            "Build the Bigger Core",
            "ae2:storage_component_16k",
            "Craft a 16k Storage Component as the basis of a larger storage cell.",
            52,
            -2,
        )
        .depends_on(larger_cells)
        .item("ae2:storage_component_16k")
        .finish()
    )

    cell_housing = (
        chapter.quest(
            "cell_housing",
            "Reusable Cell Housing",
            "ae2:item_cell_housing",
            (
                "Craft an Item Cell Housing. Cell components can be installed in housings and later "
                "recovered when the network is reorganized."
            ),
            52,
            2,
        )
        .depends_on(larger_cells)
        .item("ae2:item_cell_housing")
        .finish()
    )

    cell_workbench = (
        chapter.quest(
            "cell_workbench",
            "Partition the Storage",
            "ae2:cell_workbench",
            (
                "Craft a Cell Workbench. It configures storage cells with filters and copies settings "
                "between cells and memory cards."
            ),
            54,
            0,
        )
        .depends_on(storage_components, cell_housing)
        .item("ae2:cell_workbench")
        .finish()
    )

    partition_cell = (
        chapter.quest(
            "partition_cell",
            "A Cell with a Purpose",
            "ae2:item_storage_cell_16k",
            (
                "Use the Cell Workbench to partition a storage cell for a deliberate group of items, "
                "such as ores, mob drops, or building materials."
            ),
            56,
            0,
        )
        .depends_on(cell_workbench)
        .checkmark()
        .finish()
    )

    import_bus = (
        chapter.quest(
            "import_bus",
            "Pull Items into the Network",
            "ae2:import_bus",
            "Craft an Import Bus to transfer items from an adjacent inventory into ME storage.",
            52,
            5,
        )
        .depends_on(larger_cells)
        .item("ae2:import_bus")
        .finish()
    )

    export_bus = (
        chapter.quest(
            "export_bus",
            "Push Items Where Needed",
            "ae2:export_bus",
            "Craft an Export Bus to keep an adjacent inventory supplied with selected network items.",
            54,
            5,
        )
        .depends_on(import_bus)
        .item("ae2:export_bus")
        .finish()
    )

    (
        chapter.quest(
            "bus_upgrades",
            "Faster and Smarter Buses",
            "ae2:speed_card",
            (
                "Upgrade an import or export bus with acceleration and capacity improvements. Filters, "
                "redstone control, and fuzzy matching can make automation safer and more precise."
            ),
            56,
            5,
            optional=True,
        )
        .depends_on(export_bus)
        .item("ae2:speed_card", 2)
        .finish()
    )

    level_emitter = (
        chapter.quest(
            "level_emitter",
            "React to Stock Levels",
            "ae2:level_emitter",
            (
                "Craft a Level Emitter and configure it to output redstone when a chosen item rises "
                "above or falls below a target amount."
            ),
            58,
            4,
        )
        .depends_on(export_bus)
        .item("ae2:level_emitter")
        .finish()
    )

    stock_control = (
        chapter.quest(
            "stock_control",
            "Produce Only What Is Needed",
            "ae2:level_emitter",
            (
                "Use a Level Emitter with a machine or crafting setup to maintain a useful stock level "
                "without producing endlessly."
            ),
            60,
            4,
        )
        .depends_on(level_emitter)
        .checkmark()
        .finish()
    )

    p2p_tunnel = (
        chapter.quest(
            "p2p_tunnel",
            "Tunnel the Network",
            "ae2:me_p2p_tunnel",
            (
                "Craft ME P2P Tunnels. A linked input and output can transport many channels through a "
                "single carrier network, simplifying large controller layouts."
            ),
            58,
            -3,
        )
        .depends_on(partition_cell)
        .item("ae2:me_p2p_tunnel", 2)
        .finish()
    )

    memory_card = (
        chapter.quest(
            "memory_card",
            "Copy the Link",
            "ae2:memory_card",
            "Craft a Memory Card and use it to link a pair of P2P tunnel endpoints.",
            60,
            -3,
        )
        .depends_on(p2p_tunnel)
        .item("ae2:memory_card")
        .finish()
    )

    p2p_channels = (
        chapter.quest(
            "p2p_channels",
            "Thirty-Two Channels Through One Line",
            "ae2:me_p2p_tunnel",
            (
                "Route a dense-cable branch through a linked ME P2P tunnel pair and confirm that the "
                "remote side receives the intended channel capacity."
            ),
            62,
            -3,
        )
        .depends_on(memory_card)
        .checkmark()
        .finish()
    )

    subnetwork = (
        chapter.quest(
            "subnetwork",
            "A Network within the Network",
            "ae2:quartz_fiber",
            (
                "Build a small subnetwork with its own channel budget. Use Quartz Fiber, an Interface, "
                "or a Storage Bus to share power or inventory access without merging channels."
            ),
            64,
            -1,
        )
        .depends_on(p2p_channels, stock_control)
        .checkmark()
        .finish()
    )

    wireless_access_point = (
        chapter.quest(
            "wireless_access_point",
            "Network Access without a Cable",
            "ae2:wireless_access_point",
            "Craft a Wireless Access Point and connect it to a powered, channel-carrying network line.",
            58,
            8,
        )
        .depends_on(larger_cells)
        .item("ae2:wireless_access_point")
        .finish()
    )

    wireless_terminal = (
        chapter.quest(
            "wireless_terminal",
            "Storage in Your Hand",
            "ae2:wireless_terminal",
            "Craft and link a Wireless Terminal so ME storage can be accessed around the base.",
            60,
            8,
        )
        .depends_on(wireless_access_point)
        .item("ae2:wireless_terminal")
        .finish()
    )

    (
        chapter.quest(
            "wireless_range",
            "Extend the Signal",
            "ae2:wireless_booster",
            "Add Wireless Boosters to increase the access point's usable range.",
            62,
            8,
            optional=True,
        )
        .depends_on(wireless_terminal)
        .item("ae2:wireless_booster", 4)
        .finish()
    )

    (
        chapter.quest(
            "security_terminal",
            "Secure the Network",
            "ae2:security_station",
            (
                "Craft a Security Station and review its permission system. Security becomes important "
                "when wireless access, automation, or multiple players share one network."
            ),
            64,
            7,
            optional=True,
        )
        .depends_on(wireless_terminal)
        .item("ae2:security_station")
        .finish()
    )

    advanced_network = (
        chapter.quest(
            "advanced_network",
            "An Organized Digital Base",
            "ae2:controller",
            (
                "Combine partitioned cells, controlled imports and exports, channel routing, and remote "
                "access into one dependable network that remains understandable as it grows."
            ),
            66,
            2,
        )
        .depends_on(subnetwork, wireless_terminal)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "ae2_mastery",
            "Master of the ME Network",
            "ae2:dense_smart_cable",
            (
                "You can now scale digital storage, automate inventory movement, control stock levels, "
                "route channels through P2P tunnels, isolate subnetworks, and access the system wirelessly."
            ),
            68,
            2,
        )
        .depends_on(advanced_network)
        .checkmark()
        .reward_item("ae2:fluix_crystal", 16)
        .finish()
    )
